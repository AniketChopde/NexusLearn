from typing import List, Dict, Any
from loguru import logger
import asyncio
import json

from services.azure_openai import azure_openai_service
from services.duckduckgo_search import search_service
from utils.helpers import parse_json_markdown

class CourseRecommendationAgent:
    """Agent responsible for recommending courses from external platforms."""
    
    def __init__(self):
        self.agent_name = "Course Recommendation Agent"
        self.temperature = 0.7
    
    async def recommend_courses(
        self,
        exam_type: str,
        current_knowledge: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Recommend courses based on exam type and user knowledge.
        
        Args:
            exam_type: Type of exam (e.g., GATE IT, JEE Main)
            current_knowledge: User's current knowledge level
            
        Returns:
            List of recommended courses
        """
        try:
            # Step 1: Generate search queries using LLM
            system_prompt = """You are an expert educational counselor.
            Generate 3-4 highly specific search queries to find the best FREE or high-quality video courses/playlists for the given exam.
            Focus on platforms like YouTube, Coursera, NPTEL, or EdX.
            
            Return ONLY a JSON object:
            {
                "queries": [
                    "exact search query 1",
                    "exact search query 2"
                ]
            }
            """
            
            user_prompt = f"""
            Exam: {exam_type}
            User Level: {json.dumps(current_knowledge or {}, indent=2)}
            
            Generate queries to find full course playlists or comprehensive tutorials.
            Example queries: "GATE CS complete playlist", "JEE Main Physics full course vedantu", "NPTEL DBMS for GATE"
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            
            queries = parse_json_markdown(response).get("queries", [])
            logger.info(f"Generated course search queries for {exam_type}: {queries}")
            
            # Step 2: Search for courses using generated queries
            all_courses = []
            seen_urls = set()
            
            for query in queries:
                results = await search_service.search(query, max_results=4)
                
                for res in results:
                    if res["url"] in seen_urls:
                        continue
                        
                    # Basic filtering for course-like content
                    title_lower = res["title"].lower()
                    if any(x in title_lower for x in ["course", "playlist", "tutorial", "full", "complete", "lecture"]):
                        seen_urls.add(res["url"])
                        
                        # Determine platform
                        platform = "Web"
                        if "youtube.com" in res["url"] or "youtu.be" in res["url"]:
                            platform = "YouTube"
                        elif "coursera.org" in res["url"]:
                            platform = "Coursera"
                        elif "udemy.com" in res["url"]:
                            platform = "Udemy"
                        elif "nptel" in res["url"] or "swayam" in res["url"]:
                            platform = "NPTEL"
                            
                        all_courses.append({
                            "title": res["title"],
                            "description": res["snippet"],
                            "url": res["url"],
                            "platform": platform,
                            "thumbnail": None  # Placeholder, could extract from YouTube API later
                        })
            
            # Step 3: Deduplicate and limit
            # (already deduplicated by URL, just limiting count)
            return all_courses[:10]
            
        except Exception as e:
            logger.error(f"Error recommending courses: {str(e)}")
            return []

# Global instance
course_recommendation_agent = CourseRecommendationAgent()
