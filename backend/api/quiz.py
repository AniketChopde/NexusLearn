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
    QuizResponse, QuizResultResponse, TestCenterGenerate
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

@router.post("/test-center", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def start_test_center(
    test_data: TestCenterGenerate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a full exam simulation in the Test Center."""
    try:
        from agents.search_agent import search_agent
        
        logger.info(f"Test Center started for exam: {test_data.exam_name}")
        
        # 1. Fetch exam rules and pattern
        exam_info = await search_agent.search_exam_pattern(test_data.exam_name)
        pattern = exam_info.get("exam_pattern", {})
        duration = pattern.get("duration_minutes", 180)
        
        # Determine total question target
        total_q_target = pattern.get("total_questions")
        q_per_subject = pattern.get("questions_per_subject", {})
        
        logger.info(f"Extracted info for {test_data.exam_name}: total_q={total_q_target}, duration={duration}")
        
        # Hardcoded defaults for common exams if search fails to be specific
        exam_name_upper = test_data.exam_name.upper()
        if not total_q_target or total_q_target < 50: # Real simulations are usually 50+ questions
            logger.warning(f"Suspicously low question count ({total_q_target}) for {test_data.exam_name}. Using known defaults.")
            if "JEE" in exam_name_upper:
                total_q_target = 75
                q_per_subject = {"Physics": 25, "Chemistry": 25, "Maths": 25}
            elif "GATE" in exam_name_upper:
                total_q_target = 65
            elif "NEET" in exam_name_upper:
                total_q_target = 180
            elif "UPSC" in exam_name_upper:
                total_q_target = 100
            else:
                total_q_target = max(30, total_q_target or 0) # General minimum
            
        subjects = exam_info.get("syllabus_overview", {}).get("subjects", ["General"])
        topics_per_subject = exam_info.get("syllabus_overview", {}).get("topics_per_subject", {})
        
        
        all_questions = []
        import asyncio
        tasks = []
        
        # OPTIMIZED: Use new fast method instead of individual topic calls
        # This reduces from 9 parallel tasks to 3-5 batch tasks
        logger.info(f"⚡ Using OPTIMIZED Test Center generation")
        
        # 2. Strategy: Batch questions by subject for faster generation
        if q_per_subject and any(sub in q_per_subject for sub in subjects):
            logger.info(f"Using subject-wise distribution for {test_data.exam_name}: {q_per_subject}")
            
            for subject, count in q_per_subject.items():
                # Generate ALL questions for this subject in ONE call
                logger.info(f"⚡ Batching {count} questions for {subject}")
                tasks.append(
                    quiz_agent.generate_test_center_questions(
                        topic=subject,
                        count=count,
                        exam_type=test_data.exam_name
                    )
                )
        else:
            # Even distribution - generate in larger batches
            all_important_topics = []
            for sub in subjects:
                sub_topics = topics_per_subject.get(sub, [])
                if not sub_topics:
                    all_important_topics.append((sub, "Advanced Concepts"))
                for t in sub_topics[:4]:
                    all_important_topics.append((sub, t))
            
            if not all_important_topics:
                all_important_topics = [("General", "Core Concepts")]
                
            # OPTIMIZATION: Batch into 3-5 calls instead of 9-15
            target_topics = all_important_topics[:5]  # Reduced from 15
            q_per_topic = max(10, total_q_target // len(target_topics))  # Larger batches
            
            logger.info(f"⚡ Batching {total_q_target} questions across {len(target_topics)} calls ({q_per_topic} each)")
            
            for sub, topic in target_topics:
                tasks.append(
                    quiz_agent.generate_test_center_questions(
                        topic=f"{sub} {topic}",
                        count=q_per_topic,
                        exam_type=test_data.exam_name
                    )
                )

        logger.info(f"⚡ Generating ~{total_q_target} questions for {test_data.exam_name} across {len(tasks)} OPTIMIZED batch tasks")
        topic_results = await asyncio.gather(*tasks)
        for i, qr in enumerate(topic_results):
            logger.info(f"Task {i} returned {len(qr)} questions")
            all_questions.extend(qr)
        
        # 3. Validation and Fallback: If we are significantly short, generate more general questions
        if len(all_questions) < total_q_target * 0.9:
            needed = total_q_target - len(all_questions)
            logger.warning(f"Short on questions ({len(all_questions)}/{total_q_target}). Generating {needed} more to meet target.")
            more_qs = await quiz_agent.generate_questions(
                topic=f"Advanced {test_data.exam_name} {subjects[0] if subjects else ''} numericals and conceptuals",
                count=needed,
                difficulty="hard",
                exam_type=test_data.exam_name
            )
            all_questions.extend(more_qs)

        # Final trim to exact target
        all_questions = all_questions[:total_q_target]
        logger.info(f"Final simulation prepared with {len(all_questions)} questions")
        
        # 4. Create Quiz Session with Time Limit
        quiz_session = QuizSession(
            user_id=current_user.user_id,
            topic=test_data.exam_name,
            subject=subjects[0] if subjects else "General",
            difficulty="hard",
            questions=all_questions,
            total_questions=len(all_questions),
            time_limit_minutes=duration
        )
        
        db.add(quiz_session)
        await db.commit()
        await db.refresh(quiz_session)
        
        return quiz_session

    except Exception as e:
        logger.error(f"Error starting test center: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Test Center: {str(e)}"
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


@router.get("/history", response_model=List[QuizResponse])
async def get_quiz_history(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get quiz history for current user."""
    try:
        result = await db.execute(
            select(QuizSession).where(QuizSession.user_id == current_user.user_id)
        )
        quizzes = result.scalars().all()
        return quizzes
    
    except Exception as e:
        logger.error(f"Error fetching quiz history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quiz history"
        )
