"""
Orchestrator Agent for coordinating complex workflows across specialized agents.
"""

import asyncio
from typing import List, Dict, Any
from loguru import logger
from datetime import datetime, timedelta

from agents.search_agent import search_agent
from agents.planning_agent import planning_agent
from agents.content_agent import content_agent
from agents.quiz_agent import quiz_agent
from agents.gap_analysis_agent import gap_analysis_agent
from agents.content_filter_agent import content_filter_agent
from services.vector_store import vector_store_service
from agents.safety_agent import safety_agent


class AgentOrchestrator:
    """Agent responsible for multi-agent coordination."""
    
    def __init__(self):
        """Initialize Orchestrator."""
        self.agent_name = "Orchestrator Agent"
    
    async def handle_exam_preparation(
        self,
        exam_type: str,
        target_date: str,
        daily_hours: int,
        user_goal: str = None,
        current_knowledge: Dict[str, Any] = None,
        fast_learn: bool = False
    ) -> Dict[str, Any]:
        """
        Create a study plan for any learning goal (exam, skill, or subject).
        """
        try:
            logger.info(f"Starting study plan workflow for {exam_type} (Fast Learn: {fast_learn})")
            
            # Step 1: Skip internet search for syllabus as per user request (User wants LLM-only)
            logger.info("Step 1: Using LLM internal knowledge for syllabus (Internet search skipped)...")
            exam_info = {} # We'll let planning agent use its knowledge
            
            # Step 2: Analyze goal and feasibility
            logger.info("Step 2: Analyzing user goal...")
            goal_analysis = await planning_agent.analyze_user_goal(
                goal=user_goal or f"Learn {exam_type} by {target_date} with {daily_hours} hours daily",
                exam_type=exam_type,
                target_date=target_date,
                daily_hours=daily_hours,
                current_knowledge=current_knowledge or {}
            )
            
            # Step 3: Create study plan
            logger.info("Step 3: Creating study plan...")
            study_plan = await planning_agent.create_study_plan(
                exam_type=exam_type,
                target_date=target_date,
                daily_hours=daily_hours,
                syllabus_data=None, # Explicitly None to use LLM knowledge only
                current_knowledge=current_knowledge or {},
                goal=user_goal,
                fast_learn=fast_learn
            )
            
            # Step 4: Generate immediate actions
            logger.info("Step 4: Generating immediate actions...")
            immediate_actions = await planning_agent.get_immediate_actions(
                study_plan=study_plan
            )
            
            result = {
                "exam_info": exam_info,
                "goal_analysis": goal_analysis,
                "study_plan": study_plan,
                "immediate_actions": immediate_actions,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Study plan workflow completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in handle_exam_preparation: {str(e)}")
            raise
    
    async def ensure_topic_indexed(
        self,
        module_id: str,
        topic: str,
        exam_type: str,
        module_name: str,
    ) -> bool:
        """Ensures a topic is indexed, fetching and processing content if needed."""
        if vector_store_service.get_context_length(module_id) > 0:
            logger.info(f"Topic '{topic}' is already indexed for module '{module_id}'.")
            return True

        try:
            # Check if already indexed
            if vector_store_service.get_context_length(module_id) > 20:
                logger.info(f"Topic '{topic}' already indexed with {vector_store_service.get_context_length(module_id)} chunks, skipping re-index")
                return True

            logger.info(f"Auto-indexing topic: '{topic}' for module: {module_id}")
            raw_resources = await search_agent.research_module_content(module_name, topic)
            if not raw_resources:
                logger.warning(f"No raw resources found for topic: {topic}")
                return False

            clean_docs = await content_filter_agent.filter_and_format(
                exam_type, module_name, topic, raw_resources
            )
            if not clean_docs:
                logger.warning(f"No clean documents produced for topic: {topic}")
                return False

            await vector_store_service.add_documents(module_id, clean_docs)
            logger.info(f"Successfully auto-indexed topic: '{topic}'")
            return True
        except Exception as e:
            logger.error(f"Error during auto-indexing for topic '{topic}': {e}")
            return False

    async def handle_topic_learning(
        self,
        module_id: str,
        topic: str,
        exam_type: str = "General",
        module_name: str = "Specific Module"
    ) -> Dict[str, Any]:
        """
        Complete topic learning workflow with RAG pipeline.
        """
        try:
            logger.info(f"Starting RAG-based learning flow for: {topic}")
            
            # Ensure topic is indexed before proceeding
            await self.ensure_topic_indexed(
                module_id=module_id,
                topic=topic,
                exam_type=exam_type,
                module_name=module_name,
            )

            # Step 4: Teaching Agent (Grounded Explanation)
            logger.info("Step 4: Teaching Agent generating explanation...")
            explanation = await content_agent.explain_concept(
                module_id=module_id,
                topic=topic,
                module_name=module_name
            )
            
            # Step 5: Quiz Agent (Grounded Quiz)
            logger.info("Step 5: Quiz Agent creating assessment...")
            quiz_questions = await quiz_agent.generate_questions(
                module_id=module_id,
                topic=topic,
                count=5,
                exam_type=exam_type
            )
            
            # Use explanation as base and update with meta info (Flattening structure for Frontend)
            result = explanation
            result.update({
                "quiz": quiz_questions,
                "source_grounded": True,
                "created_at": datetime.utcnow().isoformat()
            })
            # Ensure topic is strictly set from the loop variable
            result["topic"] = topic
            
            logger.info("RAG learning workflow completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in handle_topic_learning: {str(e)}")
            raise

    
    async def handle_performance_review(
        self,
        user_id: str,
        quiz_results: list,
        progress_data: list
    ) -> Dict[str, Any]:
        """
        Complete performance review workflow.
        """
        try:
            logger.info(f"Starting performance review for user: {user_id}")
            
            # Step 1: Analyze performance
            logger.info("Step 1: Analyzing performance...")
            performance_analysis = await gap_analysis_agent.analyze_performance(
                quiz_results=quiz_results,
                user_id=user_id
            )
            
            # Step 2: Identify weak areas
            logger.info("Step 2: Identifying weak areas...")
            user_history = {
                "quiz_results": quiz_results,
                "progress": progress_data
            }
            weak_areas = await gap_analysis_agent.identify_weak_areas(user_history)
            
            # Step 3: Generate focus recommendations
            logger.info("Step 3: Generating recommendations...")
            focus_plan = await gap_analysis_agent.suggest_focus_areas(
                gaps=weak_areas,
                time_available_hours=10
            )
            
            # Step 4: Create personalized guidance
            logger.info("Step 4: Creating personalized guidance...")
            weak_topics = [area.get("topic") for area in weak_areas[:5]]
            guidance = await gap_analysis_agent.generate_personalized_guidance(
                weak_areas=weak_topics,
                learning_style="visual"
            )
            
            result = {
                "performance_analysis": performance_analysis,
                "weak_areas": weak_areas,
                "focus_plan": focus_plan,
                "personalized_guidance": guidance,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Performance review completed successfully")
            return result
        
        except Exception as e:
            logger.error(f"Error in handle_performance_review: {str(e)}")
            raise

    async def handle_chapter_teaching(
        self,
        chapter_id: str,
        chapter_name: str,
        topics: List[str],
        exam_type: str = "General",
        enable_rag: bool = False  # RAG is now optional for speed
    ) -> Dict[str, Any]:
        """
        Optimized chapter teaching workflow - generates ONLY teaching content.
        Quiz generation is moved to separate endpoint for better performance.
        
        Performance: ~30s vs 5min (10x faster)
        """
        try:
            logger.info(f"🚀 Starting OPTIMIZED teaching workflow for: {chapter_name} (RAG={enable_rag})")
            
            # Generate teaching content for all topics in parallel
            # WITHOUT quiz generation and WITHOUT RAG (unless explicitly requested)
            async def generate_topic_explanation(topic: str):
                """Generate explanation for a single topic."""
                module_id = f"{chapter_id}_{topic.replace(' ', '_')}"
                
                # Optional: Do RAG only if enabled
                if enable_rag:
                    logger.info(f"🔍 RAG enabled for: {topic}")
                    await self.ensure_topic_indexed(
                        module_id=module_id,
                        topic=topic,
                        exam_type=exam_type,
                        module_name=chapter_name
                    )
                    # Generate grounded explanation
                    explanation = await content_agent.explain_concept(
                        module_id=module_id,
                        topic=topic,
                        module_name=chapter_name
                    )
                else:
                    # Fast path: Direct LLM explanation without RAG
                    logger.info(f"⚡ Fast explanation (no RAG) for: {topic}")
                    explanation = await content_agent.explain_concept_fast(
                        topic=topic,
                        exam_type=exam_type,
                        context=chapter_name
                    )
                
                
                # Return complete explanation with all fields
                result = {
                    "topic": topic,
                    "source_grounded": enable_rag,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # Merge all explanation fields
                result.update(explanation)
                
                return result
            
            # Execute all topics in parallel
            tasks = [generate_topic_explanation(topic) for topic in topics]
            topic_lessons = await asyncio.gather(*tasks)
            
            logger.info(f"✅ Teaching content generated for {len(topics)} topics in chapter '{chapter_name}'")
                
            return {
                "chapter_name": chapter_name,
                "topic_lessons": topic_lessons,
                "teaching_completed_at": datetime.utcnow().isoformat(),
                "source_grounded": enable_rag,
                "quiz_note": "Quiz generation moved to separate endpoint - click 'Generate Quiz' button"
            }
            
        except Exception as e:
            logger.error(f"❌ Error in handle_chapter_teaching: {str(e)}")
            raise



# Global orchestrator instance
orchestrator = AgentOrchestrator()
