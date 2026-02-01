"""
Planning Agent for creating comprehensive study plans.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
import json

from services.azure_openai import azure_openai_service
from utils.helpers import parse_json_markdown


class PlanningAgent:
    """Agent responsible for creating and managing study plans."""
    
    def __init__(self):
        """Initialize Planning Agent."""
        self.agent_name = "Planning Agent"
        self.temperature = 0.7
    
    async def analyze_user_goal(
        self,
        goal: str,
        exam_type: str = "General",
        target_date: Any = None,
        daily_hours: int = 2,
        current_knowledge: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze user's goal and create initial assessment.
        
        Args:
            goal: User's study goal
            exam_type: Type of exam
            target_date: Target exam date
            daily_hours: Daily study hours available
            current_knowledge: User's current knowledge level
        
        Returns:
            Analysis with recommendations
        """
        try:
            # Ensure target_date is a datetime/date object
            if target_date is None:
                target_date_obj = (datetime.now() + timedelta(days=30)).date()
            elif isinstance(target_date, str):
                try:
                    # Handle common ISO formats
                    clean_date = target_date.replace('Z', '+00:00')
                    target_date_obj = datetime.fromisoformat(clean_date).date()
                except ValueError:
                    target_date_obj = (datetime.now() + timedelta(days=30)).date()
            elif isinstance(target_date, datetime):
                target_date_obj = target_date.date()
            else:
                target_date_obj = target_date
                
            days_until_exam = (target_date_obj - datetime.now().date()).days
            # Ensure at least 1 day to avoid division/zero errors
            days_until_exam = max(1, days_until_exam)
            total_hours = days_until_exam * daily_hours
            
            system_prompt = f"""You are an expert study planner specializing in competitive exam preparation.
            Analyze the user's goal and provide a structured assessment.
            
            Return your response as a JSON object with the following structure:
            {{
                "feasibility": "high/medium/low",
                "recommended_approach": "intensive/moderate/relaxed",
                "key_focus_areas": ["area1", "area2", ...],
                "estimated_coverage": "percentage of syllabus achievable",
                "recommendations": ["recommendation1", "recommendation2", ...]
            }}
            
            OUTPUT INSTRUCTIONS:
            - Output ONLY raw JSON.
            - Do NOT include any conversational text.
            """
            
            user_prompt = f"""
            Goal: {goal}
            Exam Type: {exam_type}
            Days Until Exam: {days_until_exam}
            Daily Study Hours: {daily_hours}
            Total Available Hours: {total_hours}
            Current Knowledge: {json.dumps(current_knowledge or {}, indent=2)}
            
            Provide a comprehensive analysis of this study plan taking into account the user's current knowledge.
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )
            
            analysis = parse_json_markdown(response)
            analysis["days_until_exam"] = days_until_exam
            analysis["total_hours"] = total_hours
            
            logger.info(f"Goal analysis completed for {exam_type}")
            return analysis
        
        except Exception as e:
            logger.error(f"Error in analyze_user_goal: {str(e)}")
            raise
    
    async def create_study_plan(
        self,
        exam_type: str,
        target_date: Any,
        daily_hours: int,
        syllabus_data: Any = None,
        current_knowledge: Dict[str, Any] = None,
        goal: str = None,
        fast_learn: bool = False
    ) -> Dict[str, Any]:
        """
        Create a comprehensive study plan.
        """
        try:
            # Ensure target_date is a datetime/date object
            if target_date is None:
                target_date_obj = (datetime.now() + timedelta(days=90)).date()
            elif isinstance(target_date, str):
                try:
                    clean_date = target_date.replace('Z', '+00:00')
                    target_date_obj = datetime.fromisoformat(clean_date).date()
                except ValueError:
                    target_date_obj = (datetime.now() + timedelta(days=90)).date()
            elif isinstance(target_date, datetime):
                target_date_obj = target_date.date()
            else:
                target_date_obj = target_date
                
            days_until_exam = (target_date_obj - datetime.now().date()).days
            days_until_exam = max(1, days_until_exam)
            
            fast_learn_instruction = ""
            if fast_learn:
                fast_learn_instruction = """
                FAST LEARN MODE (CRITICAL):
                - Prioritize ONLY topics with high weightage in the exam.
                - Skip low-weightage or optional topics.
                - Focus on maximizing score in minimum time.
                - Ensure even with fewer topics, the pedagogical sequence remains logical.
                """
            
            system_prompt = f"""ROLE: Expert Pedagogical Planner Agent
            
            INPUT:
            - Exam name: {exam_type}
            - User level & Goal: {goal or "General Prep"}
            - Available time: {days_until_exam} days
            - Mode: {'Fast Learn (High Weightage)' if fast_learn else 'Standard'}
            
            TASK:
            Generate a module-wise syllabus-aligned study plan for {exam_type}.
            {fast_learn_instruction}
            
            CRITICAL SEQUENCING RULES:
            1. PEDAGOGICAL FLOW: You MUST order modules in a logical pedagogical sequence.
            2. Master building blocks before tackling complex topics.
            
            CONSTRAINTS:
            - If Syllabus data is provided, use it. IF NOT, use your internal expertise to determine the standard syllabus for {exam_type}.
            - Do NOT add extra unrelated topics.
            - Do NOT use internet.
            
            OUTPUT:
            Structured JSON:
            {{
              "exam": "{exam_type}",
              "is_fast_learn": {str(fast_learn).lower()},
              "modules": [
                {{
                  "module_name": "Logical Step Name",
                  "estimated_days": "days",
                  "difficulty": "Easy/Medium/Hard",
                  "topics": ["topic1", "topic2"],
                  "pedagogical_reasoning": "Reasoning for sequence and weightage"
                }}
              ]
            }}
            
            OUTPUT INSTRUCTIONS:
            - Output ONLY raw JSON.
            - Do NOT include any conversational text.
            """
            
            user_prompt = f"""
            Exam Type: {exam_type}
            User Goal: {goal or f"Prepare for {exam_type}"}
            Days Until Exam: {days_until_exam}
            Daily Study Hours: {daily_hours}
            Syllabus: {json.dumps(syllabus_data, indent=2) if syllabus_data else "Determine standard syllabus based on your knowledge"}
            Current Knowledge: {json.dumps(current_knowledge or {}, indent=2)}
            
            Generate the structured module-wise study plan.
            """
            
            response = await azure_openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            study_plan = parse_json_markdown(response)
            logger.info(f"Study plan created for {exam_type}")
            return study_plan
        
        except Exception as e:
            logger.error(f"Error in create_study_plan: {str(e)}")
            raise
    
    async def breakdown_chapters(
        self,
        subject: str,
        chapter_name: str,
        estimated_hours: int
    ) -> Dict[str, Any]:
        """
        Break down a chapter into detailed topics and sub-topics.
        
        Args:
            subject: Subject name
            chapter_name: Chapter name
            estimated_hours: Estimated hours for this chapter
        
        Returns:
            Detailed chapter breakdown
        """
        try:
            system_prompt = """You are an expert educator creating detailed chapter breakdowns.
            
            Return your response as a JSON object with the following structure:
            {
                "topics": [
                    {
                        "topic_name": "name",
                        "subtopics": ["subtopic1", "subtopic2"],
                        "estimated_hours": number,
                        "difficulty": "easy/medium/hard",
                        "prerequisites": ["prerequisite1", "prerequisite2"],
                        "key_concepts": ["concept1", "concept2"]
                    }
                ],
                "learning_objectives": ["objective1", "objective2"],
                "recommended_sequence": ["topic1", "topic2", ...]
            }"""
            
            user_prompt = f"""
            Subject: {subject}
            Chapter: {chapter_name}
            Total Estimated Hours: {estimated_hours}
            
            Create a detailed breakdown of this chapter into topics and subtopics.
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5
            )
            
            breakdown = parse_json_markdown(response)
            logger.info(f"Chapter breakdown created for {chapter_name}")
            return breakdown
        
        except Exception as e:
            logger.error(f"Error in breakdown_chapters: {str(e)}")
            raise
    
    async def get_immediate_actions(
        self,
        study_plan: Dict[str, Any]
    ) -> List[str]:
        """
        Get immediate next steps from study plan.
        
        Args:
            study_plan: Complete study plan
        
        Returns:
            List of immediate action items
        """
        try:
            system_prompt = """Extract the top 5 immediate action items from this study plan.
            Return as a JSON object: {"actions": ["action1", "action2", ...]}"""
            
            user_prompt = f"Study Plan: {json.dumps(study_plan, indent=2)}"
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            result = parse_json_markdown(response)
            return result.get("actions", [])
        
        except Exception as e:
            logger.error(f"Error in get_immediate_actions: {str(e)}")
            return []


# Global agent instance
planning_agent = PlanningAgent()
