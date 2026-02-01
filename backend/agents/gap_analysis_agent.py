"""
Gap Analysis Agent for identifying weak areas and providing recommendations.
"""

from typing import List, Dict, Any
from loguru import logger
import json
from collections import defaultdict

from services.azure_openai import azure_openai_service


class GapAnalysisAgent:
    """Agent responsible for analyzing performance gaps and recommendations."""
    
    def __init__(self):
        """Initialize Gap Analysis Agent."""
        self.agent_name = "Gap Analysis Agent"
        self.temperature = 0.3
    
    async def analyze_performance(
        self,
        quiz_results: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze quiz performance to identify patterns.
        
        Args:
            quiz_results: List of quiz results
            user_id: User identifier
        
        Returns:
            Performance analysis
        """
        try:
            if not quiz_results:
                return {
                    "message": "No quiz data available for analysis",
                    "recommendations": ["Take some quizzes to get personalized insights"]
                }
            
            # Calculate statistics
            total_quizzes = len(quiz_results)
            avg_score = sum(r.get("percentage", 0) for r in quiz_results) / total_quizzes
            
            # Topic-wise performance
            topic_performance = defaultdict(list)
            for result in quiz_results:
                topic = result.get("topic", "Unknown")
                topic_performance[topic].append(result.get("percentage", 0))
            
            topic_averages = {
                topic: sum(scores) / len(scores)
                for topic, scores in topic_performance.items()
            }
            
            # Identify weak topics
            weak_topics = [
                topic for topic, avg in topic_averages.items()
                if avg < 60
            ]
            
            # Time analysis
            avg_time_per_question = []
            for result in quiz_results:
                time_taken = result.get("time_taken_seconds", 0)
                total_questions = result.get("total_questions", 1)
                avg_time_per_question.append(time_taken / total_questions)
            
            avg_time = sum(avg_time_per_question) / len(avg_time_per_question) if avg_time_per_question else 0
            
            # Use LLM for deeper analysis
            system_prompt = """Analyze quiz performance data and provide insights.
            
            Return as JSON: {
                "overall_assessment": "assessment summary",
                "strengths": ["strength1", "strength2"],
                "weaknesses": ["weakness1", "weakness2"],
                "improvement_areas": [
                    {
                        "area": "area name",
                        "current_level": "beginner/intermediate/advanced",
                        "priority": "high/medium/low",
                        "specific_issues": ["issue1", "issue2"]
                    }
                ],
                "learning_style_insights": "insights about learning patterns"
            }"""
            
            user_prompt = f"""
            Total Quizzes: {total_quizzes}
            Average Score: {avg_score:.2f}%
            Topic Performance: {json.dumps(topic_averages, indent=2)}
            Weak Topics: {', '.join(weak_topics) if weak_topics else 'None'}
            Average Time per Question: {avg_time:.2f} seconds
            
            Provide comprehensive performance analysis.
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )
            
            analysis = json.loads(response)
            analysis["statistics"] = {
                "total_quizzes": total_quizzes,
                "average_score": round(avg_score, 2),
                "topic_performance": topic_averages,
                "weak_topics": weak_topics,
                "average_time_per_question": round(avg_time, 2)
            }
            
            logger.info(f"Performance analysis completed for user: {user_id}")
            return analysis
        
        except Exception as e:
            logger.error(f"Error in analyze_performance: {str(e)}")
            raise
    
    async def identify_weak_areas(
        self,
        user_history: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify specific weak areas from user history.
        
        Args:
            user_history: Complete user learning history
        
        Returns:
            List of weak areas with details
        """
        try:
            quiz_results = user_history.get("quiz_results", [])
            progress_data = user_history.get("progress", [])
            
            weak_areas = []
            
            # Analyze quiz results
            for result in quiz_results:
                if result.get("percentage", 100) < 60:
                    detailed_results = result.get("detailed_results", [])
                    incorrect_topics = [
                        r.get("topic") for r in detailed_results
                        if not r.get("is_correct")
                    ]
                    
                    for topic in set(incorrect_topics):
                        weak_areas.append({
                            "topic": topic,
                            "subject": result.get("subject"),
                            "score": result.get("percentage"),
                            "source": "quiz",
                            "severity": "high" if result.get("percentage", 0) < 40 else "medium"
                        })
            
            # Analyze progress data
            for progress in progress_data:
                if progress.get("completion_percentage", 100) < 50:
                    weak_areas.append({
                        "topic": progress.get("topic"),
                        "subject": progress.get("subject"),
                        "completion": progress.get("completion_percentage"),
                        "source": "progress",
                        "severity": "medium"
                    })
            
            # Use LLM to prioritize and structure
            if weak_areas:
                system_prompt = """Analyze and prioritize weak areas.
                
                Return as JSON: {
                    "prioritized_areas": [
                        {
                            "topic": "topic name",
                            "subject": "subject",
                            "priority": "high/medium/low",
                            "reason": "why this is a priority",
                            "recommended_action": "what to do"
                        }
                    ]
                }"""
                
                user_prompt = f"Weak Areas: {json.dumps(weak_areas, indent=2)}"
                
                response = await azure_openai_service.generate_structured_output(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=self.temperature
                )
                
                result = json.loads(response)
                return result.get("prioritized_areas", [])
            
            return []
        
        except Exception as e:
            logger.error(f"Error in identify_weak_areas: {str(e)}")
            return []
    
    async def suggest_focus_areas(
        self,
        gaps: List[Dict[str, Any]],
        time_available_hours: int = 10
    ) -> Dict[str, Any]:
        """
        Suggest focus areas based on identified gaps.
        
        Args:
            gaps: List of identified gaps
            time_available_hours: Available study time
        
        Returns:
            Focused study recommendations
        """
        try:
            system_prompt = f"""Create a focused study plan for the next {time_available_hours} hours.
            
            Return as JSON: {{
                "focus_plan": [
                    {{
                        "topic": "topic name",
                        "allocated_hours": number,
                        "approach": "how to study this",
                        "resources": ["resource1", "resource2"],
                        "success_criteria": "how to know you've mastered it"
                    }}
                ],
                "study_strategy": "overall strategy",
                "expected_improvement": "what to expect",
                "checkpoints": [
                    {{
                        "after_hours": number,
                        "checkpoint": "what to verify"
                    }}
                ]
            }}"""
            
            user_prompt = f"""
            Identified Gaps: {json.dumps(gaps, indent=2)}
            Available Time: {time_available_hours} hours
            
            Create an effective focus plan.
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4
            )
            
            recommendations = json.loads(response)
            logger.info(f"Focus areas suggested for {time_available_hours} hours")
            return recommendations
        
        except Exception as e:
            logger.error(f"Error in suggest_focus_areas: {str(e)}")
            raise
    
    async def generate_personalized_guidance(
        self,
        weak_areas: List[str],
        learning_style: str = "visual"
    ) -> Dict[str, Any]:
        """
        Generate personalized learning guidance.
        
        Args:
            weak_areas: List of weak topics
            learning_style: User's learning style
        
        Returns:
            Personalized guidance
        """
        try:
            system_prompt = f"""Generate personalized learning guidance for a {learning_style} learner.
            
            Return as JSON: {{
                "guidance": [
                    {{
                        "topic": "topic name",
                        "learning_approach": "specific approach for this learning style",
                        "recommended_resources": [
                            {{
                                "type": "video/article/interactive",
                                "description": "resource description",
                                "why_recommended": "reason"
                            }}
                        ],
                        "practice_strategy": "how to practice",
                        "time_estimate": "estimated time to master"
                    }}
                ],
                "general_tips": ["tip1", "tip2"],
                "motivation": "motivational message"
            }}"""
            
            user_prompt = f"""
            Weak Areas: {', '.join(weak_areas)}
            Learning Style: {learning_style}
            
            Provide personalized guidance.
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5
            )
            
            guidance = json.loads(response)
            logger.info(f"Personalized guidance generated for {len(weak_areas)} topics")
            return guidance
        
        except Exception as e:
            logger.error(f"Error in generate_personalized_guidance: {str(e)}")
            raise


# Global agent instance
gap_analysis_agent = GapAnalysisAgent()
