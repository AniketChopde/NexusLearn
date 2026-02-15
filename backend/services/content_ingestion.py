"""
Service for ingesting content from various sources (PDF, YouTube, Web)
and storing it in the vector database for RAG.
"""

from typing import List, Dict, Any, Optional
import os
import io
from fastapi import UploadFile
from loguru import logger
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.formatters import TextFormatter
import aiofiles

from services.vector_store import vector_store_service
from services.duckduckgo_search import search_service
from models.study_plan import StudyPlan

class ContentIngestionService:
    """Service for processing and ingesting learning content."""
    
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
    async def process_file(self, file: UploadFile, plan_id: str) -> Dict[str, Any]:
        """
        Process an uploaded file, save it, and ingest into vector store.
        """
        filename = file.filename
        content_type = file.content_type
        
        logger.info(f"Processing file: {filename} ({content_type}) for plan {plan_id}")
        
        # Validate supported types
        allowed_types = [
            "application/pdf", 
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "application/json"
        ]
        
        if not (content_type in allowed_types or content_type.startswith("image/")):
             raise ValueError(f"Unsupported file type: {content_type}")

        # Read content once
        content = await file.read()
        
        # Save file to disk for preview
        upload_dir = f"static/uploads/{plan_id}"
        os.makedirs(upload_dir, exist_ok=True)
        # Sanitize filename to avoid directory traversal
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(upload_dir, safe_filename)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(content)
            
        file_url = f"/api/static/uploads/{plan_id}/{safe_filename}"
        
        text_content = ""
        
        try:
            if content_type == "application/pdf":
                pdf_file = io.BytesIO(content)
                reader = PdfReader(pdf_file)
                text_content = ""
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
                    
            elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                docx_file = io.BytesIO(content)
                text_content = self._extract_text_from_docx(docx_file)

            elif content_type.startswith("image/"):
                # Use Azure OpenAI Vision to describe/transcribe the image
                import base64
                base64_image = base64.b64encode(content).decode('utf-8')
                text_content = await self._analyze_image_with_ai(base64_image, content_type)

            elif content_type.startswith("text/") or content_type == "application/json":
                text_content = content.decode("utf-8")
            
            if not text_content.strip():
                raise ValueError("No text content extracted from file")
                
            # Ingest content
            return await self._ingest_text(
                text=text_content,
                source_name=filename,
                source_type="file",
                plan_id=plan_id,
                extra_metadata={
                    "url": file_url,
                    "file_path": file_path,
                    "content_type": content_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            raise
            
    async def process_youtube_url(self, url: str, plan_id: str) -> Dict[str, Any]:
        """
        Process a YouTube URL, extract transcript, and ingest.
        """
        try:
            video_id = self._extract_youtube_id(url)
            if not video_id:
                raise ValueError("Invalid YouTube URL")
                
            logger.info(f"Processing YouTube video: {video_id} for plan {plan_id}")
            
            # Get video title (optional, difficult without API key or scraping)
            title = f"YouTube Video {video_id}"
            text_content = ""
            
            # Try to get transcript
            try:
                yta = YouTubeTranscriptApi()
                transcript = yta.fetch(video_id)
                formatter = TextFormatter()
                text_content = formatter.format_transcript(transcript)
            except (TranscriptsDisabled, NoTranscriptFound) as e:
                logger.warning(f"No transcript available for video {video_id}: {e}")
            except Exception as e:
                logger.warning(f"Failed to fetch transcript for {video_id}: {e}")
            
            # If we have text, ingest it
            if text_content:
                return await self._ingest_text(
                    text=text_content,
                    source_name=title,
                    source_type="youtube",
                    plan_id=plan_id,
                    extra_metadata={"url": url, "video_id": video_id}
                )
            else:
                 # Return result without ingestion (resource tracking only)
                 # Structure must match what api/content.py expects for 'details' or just be safe
                 return {
                    "success": False,
                    "source": title,
                    "type": "youtube",
                    "chunks_count": 0,
                    "extra_metadata": {"url": url, "video_id": video_id},
                    "message": "Video added to resources, but no transcript available for AI processing."
                 }
            
        except Exception as e:
            logger.error(f"Error processing YouTube URL {url}: {str(e)}")
            raise

    async def _ingest_text(
        self, 
        text: str, 
        source_name: str, 
        source_type: str, 
        plan_id: str,
        extra_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Chunk text and store in vector database.
        """
        # Create chunks
        chunks = self._create_chunks(text)
        logger.info(f"Created {len(chunks)} chunks from {source_name}")
        
        chunks_with_meta = []
        import time
        
        for i, chunk in enumerate(chunks):
            meta = {
                "source": source_name,
                "type": source_type,
                "chunk_index": i,
                "created_at": str(time.time())
            }
            if extra_metadata:
                meta.update(extra_metadata)
            
            chunks_with_meta.append({
                "text": chunk,
                "source": source_name,
                "url": extra_metadata.get("url", "") if extra_metadata else "",
                "metadata": meta
            })
            
        # Add to vector store
        # using plan_id as the module_id to keep content segregated by plan
        await vector_store_service.add_documents(
            module_id=str(plan_id),
            documents=chunks_with_meta
        )
        
        return {
            "success": True,
            "chunks_count": len(chunks),
            "source": source_name,
            "type": source_type
        }

    async def _analyze_image_with_ai(self, base64_image: str, mime_type: str) -> str:
        """
        Use Azure OpenAI Vision to extract text/description from image.
        """
        try:
            from services.azure_openai import azure_openai_service
            
            response = await azure_openai_service.client.chat.completions.create(
                model=azure_openai_service.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts text and describes diagrams from images for a study plan knowledge base."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Transcribe any text in this image and describe any diagrams or visuals in detail."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            raise ValueError(f"Failed to analyze image: {str(e)}")

    def _extract_text_from_docx(self, file_stream: io.BytesIO) -> str:
        """
        Extract text from DOCX file.
        """
        try:
            import docx
            doc = docx.Document(file_stream)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return '\n'.join(full_text)
        except Exception as e:
            logger.error(f"Error reading DOCX: {str(e)}")
            raise ValueError("Failed to process Word document")

    def _create_chunks(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        """
        chunks = []
        if not text:
            return chunks
            
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + self.chunk_size
            
            # Adjust end to nearest whitespace to avoid splitting words
            if end < text_len:
                while end > start and text[end] not in [' ', '\n', '.']:
                    end -= 1
                if end == start: # Force split if no whitespace found
                    end = start + self.chunk_size
            
            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap
            
        return chunks

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.
        """
        if "youtu.be" in url:
            return url.split("/")[-1]
        elif "youtube.com" in url:
            if "v=" in url:
                return url.split("v=")[1].split("&")[0]
        return None

# Global instance
content_ingestion_service = ContentIngestionService()
