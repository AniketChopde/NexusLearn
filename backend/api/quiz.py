"""
Quiz API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from loguru import logger
import uuid
from datetime import datetime

from database.connection import get_db
from models.quiz import (
    QuizSession, QuizGenerate, QuizSubmit,
    QuizResponse, QuizResultResponse, QuizHistoryEntry, TestCenterGenerate
)
from utils.auth import get_current_user, TokenData
from agents.quiz_agent import quiz_agent

router = APIRouter()


@router.post("/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    quiz_data: QuizGenerate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a new quiz."""
    try:
        # Generate questions using quiz agent
        questions = await quiz_agent.generate_questions(
            topic=quiz_data.topic,
            count=quiz_data.question_count,
            difficulty=quiz_data.difficulty,
            exam_type=quiz_data.exam_type
        )
        
        # Create quiz session
        quiz_session = QuizSession(
            user_id=current_user.user_id,
            topic=quiz_data.topic,
            subject=quiz_data.subject,
            difficulty=quiz_data.difficulty,
            questions=questions,
            total_questions=len(questions)
        )
        
        db.add(quiz_session)
        await db.commit()
        await db.refresh(quiz_session)
        
        logger.info(f"Quiz generated for user: {current_user.email}")
        return quiz_session
    
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Fast path: 20 questions, one LLM call, no search/PYQ — target <10s
TEST_CENTER_QUESTION_COUNT = 20
TEST_CENTER_DURATION_MINUTES = 60


@router.post("/test-center", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def start_test_center(
    test_data: TestCenterGenerate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a fast exam simulation (20 questions, single LLM call, under 10s)."""
    try:
        logger.info(f"Test Center started for exam: {test_data.exam_name} (fast 20Q)")
        # Single LLM call, no search_exam_pattern, no PYQ — minimal latency
        all_questions = await quiz_agent.generate_test_center_questions(
            topic=test_data.exam_name,
            count=TEST_CENTER_QUESTION_COUNT,
            exam_type=test_data.exam_name,
            skip_pyq=True,
        )
        all_questions = all_questions[:TEST_CENTER_QUESTION_COUNT]
        if len(all_questions) < TEST_CENTER_QUESTION_COUNT:
            logger.warning(f"Got {len(all_questions)} questions, expected {TEST_CENTER_QUESTION_COUNT}")
        quiz_session = QuizSession(
            user_id=current_user.user_id,
            topic=test_data.exam_name,
            subject="General",
            difficulty="hard",
            questions=all_questions,
            total_questions=len(all_questions),
            time_limit_minutes=TEST_CENTER_DURATION_MINUTES,
        )
        db.add(quiz_session)
        await db.commit()
        await db.refresh(quiz_session)
        logger.info(f"Test Center ready: {len(all_questions)} questions in <10s path")
        return quiz_session
    except Exception as e:
        logger.error(f"Error starting test center: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Test Center: {str(e)}",
        )


@router.post("/chapter/{chapter_id}/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_chapter_quiz(
    chapter_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate quiz for a chapter with PYQ (Previous Year Questions) search.
    This is NOW the ONLY place where PYQ search happens - NOT during teaching!
    
    Performance: Separated from teaching to avoid 5-minute delays
    """
    try:
        from models.study_plan import StudyPlanChapter,StudyPlan
        from agents.search_agent import search_agent
        
        logger.info(f"🎯 Generating quiz for chapter {chapter_id} (with PYQ search)")
        
        # Get chapter details
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
        
        # Get exam type from the study plan
        plan_result = await db.execute(
            select(StudyPlan).where(StudyPlan.id == chapter.plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        exam_type = plan.exam_type if plan else "General"
        
        topics = chapter.topics if isinstance(chapter.topics, list) else [chapter.topics]
        
        # ULTRA-OPTIMIZED: Generate questions for all topics in ONE BATCH
        all_questions = await quiz_agent.generate_chapter_questions(
            topics=topics,
            exam_type=exam_type,
            total_count=15 # Standard chapter quiz size
        )
        
        # Create quiz session
        quiz_session = QuizSession(
            user_id=current_user.user_id,
            topic=chapter.chapter_name,
            subject=exam_type,
            difficulty="medium",
            questions=all_questions,
            total_questions=len(all_questions)
        )
        
        db.add(quiz_session)
        await db.commit()
        await db.refresh(quiz_session)
        
        logger.info(f"✅ Chapter quiz generated: {len(all_questions)} questions")
        return quiz_session
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating chapter quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )


@router.post("/submit", response_model=QuizResultResponse)
async def submit_quiz(
    submission: QuizSubmit,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit quiz answers and get results."""
    try:
        # Get quiz session
        result = await db.execute(
            select(QuizSession).where(
                QuizSession.id == submission.quiz_id,
                QuizSession.user_id == current_user.user_id
            )
        )
        quiz_session = result.scalar_one_or_none()
        
        if not quiz_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        # Calculate score
        quiz_data = {
            "questions": quiz_session.questions,
            "answers": submission.answers
        }
        
        score_data = await quiz_agent.calculate_score(quiz_data)
        
        # Update quiz session
        quiz_session.answers = submission.answers
        quiz_session.score = score_data["percentage"]
        quiz_session.correct_answers = score_data["correct_answers"]
        quiz_session.time_taken_seconds = submission.time_taken_seconds
        quiz_session.status = "completed"
        quiz_session.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(quiz_session)
        
        logger.info(f"Quiz submitted: {submission.quiz_id}")
        
        return {
            **quiz_session.__dict__,
            "detailed_results": score_data["detailed_results"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/history", response_model=List[QuizHistoryEntry])
async def get_quiz_history(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get quiz history for current user: only completed attempts (submitted quizzes with score)."""
    try:
        result = await db.execute(
            select(QuizSession)
            .where(
                QuizSession.user_id == current_user.user_id,
                QuizSession.status == "completed",
            )
            .order_by(QuizSession.completed_at.desc(), QuizSession.created_at.desc())
        )
        quizzes = result.scalars().all()
        return quizzes
    
    except Exception as e:
        logger.error(f"Error fetching quiz history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quiz history"
        )

@router.get("/{quiz_id}", response_model=QuizResultResponse)
async def get_quiz_result(
    quiz_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed results for a specific quiz."""
    try:
        result = await db.execute(
            select(QuizSession).where(
                QuizSession.id == quiz_id,
                QuizSession.user_id == current_user.user_id
            )
        )
        quiz_session = result.scalar_one_or_none()
        
        if not quiz_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
            
        # Re-calculate detailed results since we don't store them
        # We need them for the frontend to show the detailed breakdown
        quiz_data = {
            "questions": quiz_session.questions,
            "answers": quiz_session.answers
        }
        
        # Calculate details (Score is already in DB, but we need the breakdown)
        score_data = await quiz_agent.calculate_score(quiz_data)
        
        return {
            **quiz_session.__dict__,
            "detailed_results": score_data["detailed_results"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quiz details"
        )
