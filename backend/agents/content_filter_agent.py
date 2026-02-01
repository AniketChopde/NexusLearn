import asyncio
from typing import List, Dict, Any
from loguru import logger
from services.azure_openai import azure_openai_service
from utils.helpers import parse_json_markdown, sanitize_jailbreak
import httpx
from bs4 import BeautifulSoup

class ContentFilterAgent:
    """Agent responsible for cleaning and structuring raw content (Content Filter Agent ROLE)."""
    
    def __init__(self):
        self.agent_name = "Content Filter Agent"

    def _normalize_list(self, value: Any) -> List[Dict[str, Any]]:
        if isinstance(value, list):
            return [v for v in value if isinstance(v, dict)]
        return []

    def _stringify(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        import json
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)

    def _chunk_paragraphs(self, text: str, max_chars: int = 1200) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        buf = ""
        for p in paras:
            if not buf:
                buf = p
                continue
            if len(buf) + 2 + len(p) <= max_chars:
                buf = buf + "\n\n" + p
            else:
                chunks.append(buf)
                buf = p
        if buf:
            chunks.append(buf)
        return chunks

    async def _scrub_web_content(self, url: str) -> str:
        """Fetch and extract main text from URL."""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                try:
                    response = await client.get(url)
                except httpx.ConnectError as e:
                    if "SSL" in str(e) or "certificate" in str(e):
                        logger.warning(f"SSL error for {url}, retrying without verification")
                        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as insecure_client:
                            response = await insecure_client.get(url)
                    else:
                        raise
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')
                    for tag in soup(["script", "style"]):
                        tag.decompose()
                    
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    return text[:10000]
                return ""
        except Exception as e:
            logger.error(f"Error scrubbing {url}: {str(e)}")
            return ""

    async def _process_single_result(self, res: Dict[str, Any], exam_type: str, module_name: str, topic: str) -> List[Dict[str, Any]]:
        """Helper to process a single search result."""
        url = res["url"]
        source_domain = res["source_domain"]
        source_title = res.get("title", "")
        
        raw_text = await self._scrub_web_content(url)
        if not raw_text or len(raw_text) < 200:
            return []
            
        # Sanitize text to avoid Azure Content Filter triggers (ResponsibleAIPolicyViolation)
        raw_text = sanitize_jailbreak(raw_text)

        system_prompt = f"""ROLE: Professional Content Assistant
        
        SOURCE: {source_domain}
        
        TASK:
        - Extract clean, academic notes for: {exam_type} / {module_name} / {topic}
        - Remove non-educational elements (ads, navigation, opinion)
        - Focus on definitions, formulas, and core concepts
        
        OUTPUT FORMAT:
        Return ONLY a JSON object:
        {{
          "summary": "overview",
          "sections": [
            {{
              "title": "heading",
              "key_points": ["..."],
              "content": "explanation"
            }}
          ],
          "definitions": [{{ "term": "...", "definition": "..." }}],
          "formulas": [{{ "name": "...", "formula": "...", "meaning": "..." }}],
          "examples": [{{ "prompt": "...", "solution": "..." }}],
          "metadata": {{
            "source_domain": "{source_domain}",
            "source_url": "{url}"
          }}
        }}"""
        
        user_prompt = f"Reference data from {url}:\n\n{raw_text[:8000]}"
        
        try:
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            data = parse_json_markdown(response)
            if not isinstance(data, dict):
                return []

            cleaned_docs = []
            meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
            meta = {
                **meta,
                "exam": meta.get("exam") or exam_type,
                "subject": meta.get("subject") or exam_type,
                "chapter": meta.get("chapter") or module_name,
                "topic": meta.get("topic") or topic,
                "source_domain": meta.get("source_domain") or source_domain,
                "source_url": meta.get("source_url") or url,
                "source_title": meta.get("source_title") or source_title,
            }

            summary = self._stringify(data.get("summary"))
            if summary:
                cleaned_docs.append({
                    "text": f"Summary: {summary}",
                    "source": source_domain,
                    "url": url,
                    "metadata": {**meta, "chunk_type": "summary", "section_title": None}
                })

            definitions = self._normalize_list(data.get("definitions"))
            for d in definitions:
                term = self._stringify(d.get("term")).strip()
                definition = self._stringify(d.get("definition")).strip()
                if term and definition:
                    cleaned_docs.append({
                        "text": f"Definition: {term} - {definition}",
                        "source": source_domain,
                        "url": url,
                        "metadata": {**meta, "chunk_type": "definition", "term": term, "section_title": None}
                    })

            formulas = self._normalize_list(data.get("formulas"))
            for f in formulas:
                name = self._stringify(f.get("name")).strip()
                formula = self._stringify(f.get("formula")).strip()
                meaning = self._stringify(f.get("meaning")).strip()
                if formula:
                    text = "\n".join([f"Formula: {name}" if name else "Formula:", formula, f"Meaning: {meaning}" if meaning else ""]).strip()
                    cleaned_docs.append({
                        "text": text,
                        "source": source_domain,
                        "url": url,
                        "metadata": {**meta, "chunk_type": "formula", "formula_name": name or None, "section_title": None}
                    })

            examples = self._normalize_list(data.get("examples"))
            for ex in examples:
                prompt = self._stringify(ex.get("prompt")).strip()
                solution = self._stringify(ex.get("solution")).strip()
                if prompt or solution:
                    text = "\n\n".join([p for p in [f"Example: {prompt}" if prompt else "Example:", solution] if p]).strip()
                    cleaned_docs.append({
                        "text": text,
                        "source": source_domain,
                        "url": url,
                        "metadata": {**meta, "chunk_type": "example", "section_title": None}
                    })

            sections = self._normalize_list(data.get("sections"))
            for sec in sections:
                sec_title = self._stringify(sec.get("title")).strip() or None
                key_points = sec.get("key_points") if isinstance(sec.get("key_points"), list) else []
                key_points = [self._stringify(k).strip() for k in key_points if self._stringify(k).strip()]
                content = self._stringify(sec.get("content")).strip()
                header = f"Section: {sec_title}" if sec_title else "Section:"
                kp_text = ("\n".join(["Key points:"] + [f"- {k}" for k in key_points])).strip() if key_points else ""
                section_text = "\n\n".join([p for p in [header, kp_text, content] if p]).strip()
                for part in self._chunk_paragraphs(section_text, max_chars=1400):
                    cleaned_docs.append({
                        "text": part,
                        "source": source_domain,
                        "url": url,
                        "metadata": {**meta, "chunk_type": "section", "section_title": sec_title}
                    })
            return cleaned_docs
        except Exception as e:
            logger.error(f"LLM cleaning failed for {url}: {str(e)}")
            return []

    async def filter_and_format(self, exam_type: str, module_name: str, topic: str, raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """TASK: Remove off-syllabus material and extract structured notes in parallel."""
        # Process top 5 results in parallel for speed-quality balance
        tasks = [
            self._process_single_result(res, exam_type, module_name, topic)
            for res in raw_results[:5]
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Flatten the list of lists
        all_cleaned_docs = [doc for sublist in results for doc in sublist]
        return all_cleaned_docs

content_filter_agent = ContentFilterAgent()
