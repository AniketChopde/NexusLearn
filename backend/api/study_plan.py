"""
Study Plan API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
from loguru import logger
import uuid

from database.connection import get_db
from models.study_plan import (
    StudyPlan, StudyPlanCreate, StudyPlanResponse,
    StudyPlanChapter, ChapterResponse, StudyPlanCreateResponse
)
from utils.auth import get_current_user, TokenData
from agents.orchestrator import orchestrator

router = APIRouter()


@router.post("/create", response_model=StudyPlanCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_study_plan(
    plan_data: StudyPlanCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a comprehensive study plan using multi-agent system."""
    try:
        # Use orchestrator to create comprehensive plan
        result = await orchestrator.handle_exam_preparation(
            user_goal=f"Prepare for {plan_data.exam_type}",
            exam_type=plan_data.exam_type,
            target_date=plan_data.target_date,
            daily_hours=plan_data.daily_hours,
            current_knowledge=plan_data.current_knowledge,
            fast_learn=plan_data.fast_learn
        )
        
        # Create study plan in database with full metadata
        plan_metadata = result.get("study_plan", {})
        plan_metadata["official_syllabus"] = result.get("exam_info", {})
        plan_metadata["goal_analysis"] = result.get("goal_analysis", {})
        
        study_plan = StudyPlan(
            user_id=current_user.user_id,
            exam_type=plan_data.exam_type,
            target_date=plan_data.target_date,
            daily_hours=plan_data.daily_hours,
            current_knowledge=plan_data.current_knowledge,
            plan_metadata=plan_metadata
        )
        
        db.add(study_plan)
        await db.flush()  # Get the ID without committing yet
        
        # Extract chapters from modules
        plan_data_ai = result.get("study_plan", {})
        modules = plan_data_ai.get("modules", [])
        
        # Safety fallback if AI failed completely
        if not modules:
            logger.warning(f"No modules found in AI response for {plan_data.exam_type}. Using fallback.")
            modules = [{
                "module_name": "Fundamentals & Assessment",
                "estimated_days": "7",
                "difficulty": "Medium",
                "topics": ["Exam Pattern Overview", "Current Knowledge Assessment"]
            }]

        for idx, module in enumerate(modules):
            module_name = module.get("module_name", f"Module {idx+1}")
            topics = module.get("topics", [])
            
            # Since we now use Research Agent on-demand, we don't pre-fetch all resources here
            chapter = StudyPlanChapter(
                plan_id=study_plan.id,
                chapter_name=module_name,
                subject=plan_data.exam_type,
                topics=topics,
                estimated_hours=int(float(module.get("estimated_days", 1)) * plan_data.daily_hours),
                order_index=idx,
                status="pending",
                resources=[] # Resources will be grounded via Research Agent during teaching
            )
            db.add(chapter)
            
        await db.commit()
        await db.refresh(study_plan)
        
        # Trigger background course recommendation
        try:
            from agents.course_recommendation_agent import course_recommendation_agent
            recommendations = await course_recommendation_agent.recommend_courses(
                exam_type=plan_data.exam_type,
                current_knowledge=plan_data.current_knowledge
            )
            study_plan.recommended_courses = recommendations
            await db.commit()
        except Exception as e:
            logger.error(f"Error generating course recommendations: {str(e)}")
            # Don't fail the request, just log it
        
        # Re-fetch with chapters for the response
        final_plan = await db.execute(
            select(StudyPlan)
            .where(StudyPlan.id == study_plan.id)
            .options(selectinload(StudyPlan.chapters))
        )
        plan_obj = final_plan.scalar_one()

        return {
            "study_plan": plan_obj,
            "ai_metadata": {
                "exam_info": result.get("exam_info"),
                "plan_analysis": result.get("goal_analysis"),
                "immediate_actions": result.get("immediate_actions")
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating study plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[StudyPlanResponse])
async def list_study_plans(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all study plans for current user."""
    try:
        result = await db.execute(
            select(StudyPlan)
            .where(StudyPlan.user_id == current_user.user_id)
            .options(selectinload(StudyPlan.chapters))
            .order_by(StudyPlan.created_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error listing study plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch study plans"
        )


@router.get("/{plan_id}", response_model=StudyPlanResponse)
async def get_study_plan(
    plan_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get study plan by ID."""
    try:
        result = await db.execute(
            select(StudyPlan)
            .where(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == current_user.user_id
            )
            .options(selectinload(StudyPlan.chapters))
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )
        
        return plan
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching study plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch study plan"
        )


@router.get("/{plan_id}/courses", response_model=List[Dict[str, Any]])
async def get_plan_courses(
    plan_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recommended courses for a study plan."""
    try:
        result = await db.execute(
            select(StudyPlan)
            .where(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == current_user.user_id
            )
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )
            
        # If courses are missing, generate them on-demand
        if not plan.recommended_courses:
            try:
                from agents.course_recommendation_agent import course_recommendation_agent
                recommendations = await course_recommendation_agent.recommend_courses(
                    exam_type=plan.exam_type,
                    current_knowledge=plan.current_knowledge
                )
                
                # Update database
                plan.recommended_courses = recommendations
                await db.commit()
                return recommendations
            except Exception as e:
                logger.error(f"Error generating on-demand courses: {str(e)}")
                return []
                
        return plan.recommended_courses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching plan courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch courses"
        )


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study_plan(
    plan_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a study plan."""
    try:
        result = await db.execute(
            select(StudyPlan).where(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == current_user.user_id
            )
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )
        
        await db.delete(plan)
        await db.commit()
        
        logger.info(f"Study plan deleted: {plan_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting study plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete study plan"
        )
@router.patch("/chapter/{chapter_id}", response_model=ChapterResponse)
async def update_chapter_status(
    chapter_id: uuid.UUID,
    status_data: Dict[str, str],
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update chapter status (pending, in_progress, completed)."""
    try:
        new_status = status_data.get("status")
        if new_status not in ["pending", "in_progress", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be pending, in_progress, or completed"
            )

        # Get the chapter and check ownership via plan
        result = await db.execute(
            select(StudyPlanChapter)
            .join(StudyPlan)
            .where(
                StudyPlanChapter.id == chapter_id,
                StudyPlan.user_id == current_user.user_id
            )
        )
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found"
            )
        
        chapter.status = new_status
        await db.commit()
        await db.refresh(chapter)
        
        return chapter
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chapter status: {str(e)}")
@router.post("/chapter/{chapter_id}/teach")
async def teach_chapter(
    chapter_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate teaching content for a chapter."""
    try:
        # Get chapter details with plan info
        result = await db.execute(
            select(StudyPlanChapter)
            .options(selectinload(StudyPlanChapter.study_plan))
            .join(StudyPlan)
            .where(
                StudyPlanChapter.id == chapter_id,
                StudyPlan.user_id == current_user.user_id
            )
        )
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found"
            )
        
        # If content already exists, return it
        if chapter.content and chapter.content.get("topic_lessons"):
            return chapter.content
            
        # Generate learning content using orchestrator
        teaching_content = await orchestrator.handle_chapter_teaching(
            chapter_id=str(chapter.id),
            chapter_name=chapter.chapter_name,
            topics=chapter.topics if isinstance(chapter.topics, list) else [chapter.topics],
            exam_type=chapter.study_plan.exam_type
        )
        
        # Save content to database
        chapter.content = teaching_content
        await db.commit()
        await db.refresh(chapter)
        
        return teaching_content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error teaching chapter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate teaching content"
        )
