"""
API endpoints for content management and upload.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from typing import Dict, Any, Optional
from loguru import logger

from services.content_ingestion import content_ingestion_service
from database.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth import get_current_user, TokenData
from models.study_plan import StudyPlan
from sqlalchemy import select
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_content(
    plan_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file (PDF) or add a URL (YouTube/Web) to the knowledge base.
    """
    if not file and not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file or url must be provided"
        )
        
    try:
        # Check if plan exists
        result = await db.execute(select(StudyPlan).filter(StudyPlan.id == plan_id, StudyPlan.user_id == current_user.user_id))
        plan = result.scalars().first()
        if not plan:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )

        ingestion_result = {}
        resource_entry = {}
        
        if file:
            # Validate file type
            allowed_types = [
                "application/pdf", 
                "text/plain",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "application/json",
                "image/jpeg",
                "image/png",
                "image/webp"
            ]
            if file.content_type not in allowed_types and not file.content_type.startswith("image/"):
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file.content_type}. Supported: PDF, Word, Text, Images"
                )
            
            ingestion_result = await content_ingestion_service.process_file(file, plan_id)
            # Create resource entry
            resource_entry = {
                "id": str(uuid.uuid4()),
                "title": file.filename,
                "type": "file",
                "file_type": file.content_type,
                "url": ingestion_result.get("type") == "file" and f"/api/static/uploads/{plan_id}/{file.filename}", # Fallback/Verification
                "verified_url": ingestion_result.get("extra_metadata", {}).get("url"),
                "added_at": datetime.utcnow().isoformat()
            }
            
        elif url:
            if "youtube.com" in url or "youtu.be" in url:
                ingestion_result = await content_ingestion_service.process_youtube_url(url, plan_id)
                resource_entry = {
                    "id": str(uuid.uuid4()),
                    "title": ingestion_result.get("source", "YouTube Video"),
                    "type": "youtube",
                    "url": url,
                    "added_at": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only YouTube URLs are currently supported"
                )
        
        # Update plan metadata
        current_metadata = dict(plan.plan_metadata) if plan.plan_metadata else {}
        resources = current_metadata.get("resources", [])
        
        # Use verified URL from ingestion result if available, else fallback
        if resource_entry.get("type") == "file" and not resource_entry.get("verified_url"):
             # It means ingestion didn't return URL, but we constructed it.
             # Actually process_file now returns extra_metadata with url.
             pass
        elif resource_entry.get("type") == "file":
             resource_entry["url"] = resource_entry["verified_url"] 

        resources.append(resource_entry)
        current_metadata["resources"] = resources
        
        # Re-assign to trigger update
        plan.plan_metadata = current_metadata
        
        # Force update flag if needed (SQLAlchemy sometimes needs this for JSON)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "plan_metadata")
        
        await db.commit()
                
        return {
            "status": "success",
            "message": "Content processed and added to knowledge base",
            "details": ingestion_result,
            "resource": resource_entry
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process content"
        )
