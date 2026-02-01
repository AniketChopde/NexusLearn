"""
Search Agent for gathering information using SerpApi.
"""

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from utils.helpers import parse_json_markdown, sanitize_jailbreak
import re
import httpx
from bs4 import BeautifulSoup

from services.serpapi_search import serpapi_service as search_service
from services.azure_openai import azure_openai_service


class SearchAgent:
    """Agent responsible for syllabus-aligned research (Research Agent ROLE)."""
    
    def __init__(self):
        """Initialize Search Agent."""
        self.agent_name = "Research Agent"
        self.temperature = 0.3
        self.allowed_domains = [
            "ncert.nic.in",
            "cbseacademic.nic.in",
            "khanacademy.org",
            "wikipedia.org",
            "britishcouncil.org",
            "ielts.org",
            "cambridgeenglish.org",
            "idp.com",
            "nta.ac.in",
            "education.gov.in",
            "geeksforgeeks.org",
            "tutorialspoint.com",
            "javatpoint.com",
            "byjus.com",
            "toppr.com",
            "vedantu.com"
        ]
        self.forbidden_keywords = ["blog", "quora", "forum", "reddit", "opinion"]

    async def _fetch_page_text(self, url: str, max_chars: int = 8000) -> str:
        """Fetch and extract visible text from a web page."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                try:
                    resp = await client.get(url, headers=headers)
                except httpx.ConnectError as e:
                    if "SSL" in str(e) or "certificate" in str(e):
                        logger.warning(f"SSL error for {url}, retrying without verification")
                        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False) as insecure_client:
                            resp = await insecure_client.get(url, headers=headers)
                    else:
                        raise
                except Exception:
                    return ""

            if resp.status_code != 200:
                return ""

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return ""

            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            text = " ".join(soup.get_text(" ").split())
            return text[:max_chars]
        except Exception:
            return ""

    def _infer_year(self, text: str) -> Optional[str]:
        """Infer a year like 2015-2035 from arbitrary text."""
        if not text:
            return None
        match = re.search(r"\b(20\d{2})\b", text)
        if match:
            return match.group(1)
        return None
    
    async def search_exam_pattern(self, exam_name: str) -> Dict[str, Any]:
        """
        Search for exam pattern and syllabus information.
        
        Args:
            exam_name: Name of the exam
        
        Returns:
            Structured exam information
        """
        try:
            # Search for exam pattern
            search_results = await search_service.search_exam_pattern(exam_name)
            
            if not search_results:
                logger.warning(f"No search results found for {exam_name}")
                return {
                    "exam_name": exam_name,
                    "pattern": "Information not available",
                    "sources": []
                }
            
            # Use LLM to extract structured information
            system_prompt = """You are an expert at extracting exam information from search results.
            
            Return your response as a JSON object with the following structure:
            {
                "exam_pattern": {
                    "total_marks": number,
                    "total_questions": number,
                    "questions_per_subject": {"SubjectName": number},
                    "duration_minutes": number,
                    "sections": ["section1", "section2"],
                    "question_types": ["type1", "type2"]
                },
                "syllabus_overview": {
                    "subjects": ["subject1", "subject2"],
                    "topics_per_subject": {"subject": ["topic1", "topic2"]}
                },
                "important_dates": {
                    "registration": "date or TBD",
                    "exam_date": "date or TBD"
                },
                "key_insights": ["Insight about weightage or most asked topics"]
            }"""
            
            search_text = "\n\n".join([
                f"Title: {r['title']}\nContent: {r['snippet']}\nURL: {r['url']}"
                for r in search_results[:8]
            ])
            
            user_prompt = f"""
            Exam: {exam_name}
            Search Results:
            {search_text}
            
            Extract and structure the exam pattern. 
            CRITICAL: Find the EXACT TOTAL NUMBER OF QUESTIONS in the exam. 
            If mentioned, extract how many questions per subject (e.g. Physics: 30, Math: 30, etc.).
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )
            
            exam_info = parse_json_markdown(response)
            exam_info["sources"] = [r["url"] for r in search_results[:5]]
            
            logger.info(f"Exam pattern extracted for {exam_name}")
            return exam_info
        
        except Exception as e:
            logger.error(f"Error in search_exam_pattern: {str(e)}")
            raise
    
    async def find_resources(
        self,
        topic: str,
        resource_type: str = "all"
    ) -> List[Dict[Dict[str, Any], Any]]:
        """
        Find learning resources for a topic efficiently.
        """
        try:
            # Consolidate multiple searches into one to avoid rate limits
            query = f"best {topic} learning resources tutorials videos practice"
            search_results = await search_service.search(query, max_results=10)
            
            if not search_results:
                logger.warning(f"No resources found for {topic}")
                # Fallback to general high-quality educational sites
                return [
                    {
                        "title": f"Learn {topic} on Khan Academy",
                        "snippet": f"Comprehensive video tutorials and practice exercises for {topic}.",
                        "url": f"https://www.khanacademy.org/search?page_search_query={topic}",
                        "type": "tutorial"
                    },
                    {
                        "title": f"{topic} Courses on Coursera",
                        "snippet": f"Professional courses and certifications covering {topic}.",
                        "url": f"https://www.coursera.org/courses?query={topic}",
                        "type": "tutorial"
                    }
                ]

            # Use LLM to categorize these results instead of doing multiple searches
            system_prompt = """Categorize the following search results into: 'tutorial', 'video', or 'practice'.
            Return a JSON list of objects: [{"title", "url", "snippet", "type"}]"""
            
            search_text = "\n\n".join([
                f"Title: {r['title']}\nSnippet: {r['snippet']}\nURL: {r['url']}"
                for r in search_results
            ])
            
            response = await azure_openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": search_text}
                ],
                temperature=0.3
            )
            
            resources = parse_json_markdown(response)
            if isinstance(resources, dict) and "resources" in resources:
                resources = resources["resources"]
            
            logger.info(f"Categorized {len(resources)} resources for {topic}")
            return resources if isinstance(resources, list) else []
        
        except Exception as e:
            logger.error(f"Error in find_resources: {str(e)}")
            return []
    
    async def get_latest_updates(self, exam_name: str) -> Dict[str, Any]:
        """
        Get latest updates and news about an exam.
        """
        try:
            # Simplified query
            query = f"{exam_name} current news"
            search_results = await search_service.search(query, max_results=5)
            
            if not search_results:
                return {
                    "exam_name": exam_name,
                    "updates": [],
                    "message": "No recent updates found"
                }
            
            # Use LLM to summarize updates
            system_prompt = """Summarize the latest exam updates from search results.
            
            Return as JSON: {
                "updates": [
                    {
                        "title": "update title",
                        "summary": "brief summary",
                        "date": "date if available",
                        "source": "source URL"
                    }
                ]
            }"""
            
            search_text = "\n\n".join([
                f"Title: {r['title']}\nContent: {r['snippet']}\nURL: {r['url']}"
                for r in search_results
            ])
            
            user_prompt = f"Exam: {exam_name}\n\nSearch Results:\n{search_text}"
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            updates = parse_json_markdown(response)
            logger.info(f"Latest updates retrieved for {exam_name}")
            return updates
        
        except Exception as e:
            logger.error(f"Error in get_latest_updates: {str(e)}")
            return {"exam_name": exam_name, "updates": [], "error": str(e)}
    
    async def deep_search(
        self,
        query: str,
        search_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Perform deep search with analysis.
        
        Args:
            query: Search query
            search_depth: Depth of search
        
        Returns:
            Deep search results with analysis
        """
        try:
            search_results = await search_service.deep_search(query, search_depth)
            
            # Analyze and categorize results
            all_results = (
                search_results.get("main_results", []) +
                search_results.get("related_results", [])
            )
            
            if not all_results:
                return search_results
            
            # Use LLM to categorize and summarize
            system_prompt = """Analyze and categorize search results.
            
            Return as JSON: {
                "summary": "overall summary",
                "categories": {
                    "official_sources": ["url1", "url2"],
                    "educational_content": ["url1", "url2"],
                    "community_resources": ["url1", "url2"]
                },
                "key_findings": ["finding1", "finding2"]
            }"""
            
            results_text = "\n\n".join([
                f"Title: {r['title']}\nSnippet: {r['snippet']}\nURL: {r['url']}"
                for r in all_results[:10]
            ])
            
            user_prompt = f"Query: {query}\n\nResults:\n{results_text}"
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            analysis = parse_json_markdown(response)
            search_results["analysis"] = analysis
            
            logger.info(f"Deep search completed for: {query}")
            return search_results
        
        except Exception as e:
            logger.error(f"Error in deep_search: {str(e)}")
            raise


    async def research_module_content(self, module_name: str, topic: str) -> List[Dict[str, Any]]:
        """
        ROLE: Research Agent
        TASK: Search the internet for high-quality educational content.
        """
        try:
            # General high-quality search query without site: restrictions
            query = f"{module_name} {topic} tutorial guide education"
            
            # Search broadly
            search_results = await search_service.search(query, max_results=10)
            
            results = []
            for res in search_results:
                # Basic quality filter: exclude social media/forums if needed
                if not any(k in res["url"] for k in self.forbidden_keywords):
                    results.append({
                        "title": res["title"],
                        "snippet": res["snippet"],
                        "url": res["url"],
                        "source_domain": res["url"].split("/")[2] # Extract domain for citation
                    })
            
            logger.info(f"Research Agent found {len(results)} results for {topic}")
            return results
        except Exception as e:
            logger.error(f"Error in research_module_content: {str(e)}")
            return []


    async def _extract_pyqs_from_source(self, src: Dict[str, Any], topic: str, exam_type: str) -> List[Dict[str, Any]]:
        """Helper to extract PYQs from a single search result."""
        page_text = await self._fetch_page_text(src["url"], max_chars=9000)
        if not page_text:
            return []

        # Sanitize page text
        page_text = sanitize_jailbreak(page_text)

        system_prompt = """You are a helpful assistant that identifies previous year questions (PYQs) in text.
Return JSON: {"pyqs": [{"question": "...", "exam": "...", "year": "YYYY or null", "source_url": "...", "source_title": "..."}]}
Guidelines:
- Identify and extract relevant questions.
- Prefer verified exam questions.
"""
        user_prompt = f"Topic: {topic}\nExam: {exam_type}\nData: {page_text}"
        
        try:
            resp = await azure_openai_service.generate_structured_output(system_prompt, user_prompt, temperature=self.temperature)
            parsed = parse_json_markdown(resp)
            pyqs = parsed.get("pyqs", []) if isinstance(parsed, dict) else []
            extracted = []
            for q in pyqs:
                if isinstance(q, dict) and q.get("question"):
                    extracted.append({
                        "question": q["question"].strip(),
                        "exam": q.get("exam") or exam_type,
                        "year": q.get("year") or self._infer_year(src.get("title", "")),
                        "source_url": src["url"],
                        "source_title": src["title"],
                    })
            return extracted
        except Exception:
            return []

    async def find_previous_year_questions(self, topic: str, exam_type: str) -> List[Dict[str, Any]]:
        """Parallelized search for previous year questions."""
        try:
            query = f"{exam_type} {topic} previous year questions pyq with solutions"
            results = await search_service.search(query, max_results=5)
            if not results:
                return []

            tasks = [self._extract_pyqs_from_source(src, topic, exam_type) for src in results]
            all_pyq_lists = await asyncio.gather(*tasks)
            
            flattened = [pyq for sublist in all_pyq_lists for pyq in sublist]
            logger.info(f"Parallel search found {len(flattened)} PYQs for {topic}")
            return flattened[:15]
        except Exception as e:
            logger.error(f"Error in find_previous_year_questions: {str(e)}")
            return []

    async def _extract_practice_qs_from_source(self, res: Dict[str, Any], topic: str) -> List[Dict[str, Any]]:
        """Helper to extract practice questions from a single search result."""
        page_text = await self._fetch_page_text(res["url"], max_chars=8000)
        if not page_text:
            return []
        
        # Sanitize page text
        page_text = sanitize_jailbreak(page_text)
        
        system_prompt = """Identify and extract academic questions from the reference data.
Return JSON: {"questions": [{"question": "...", "options": ["A)...", "B)...", ...], "answer": "A", "explanation": "..."}]}"""
        
        try:
            response = await azure_openai_service.generate_structured_output(system_prompt, f"Topic: {topic}\nData: {page_text}", temperature=0.3)
            parsed = parse_json_markdown(response)
            qs = parsed.get("questions", [])
            for q in qs:
                if isinstance(q, dict):
                    q["source_url"] = res["url"]
            return [q for q in qs if isinstance(q, dict)]
        except Exception:
            return []

    async def find_hard_practice_questions(self, topic: str) -> List[Dict[str, Any]]:
        """Parallelized search for hard-level practice questions."""
        try:
            query = f"hard level MCQ practice questions with solutions for {topic}"
            search_results = await search_service.search(query, max_results=5)
            
            tasks = [self._extract_practice_qs_from_source(res, topic) for res in search_results]
            all_q_lists = await asyncio.gather(*tasks)
            
            flattened = [q for sublist in all_q_lists for q in sublist]
            logger.info(f"Parallel search found {len(flattened)} practice questions for {topic}")
            return flattened[:10]
        except Exception as e:
            logger.error(f"Error in find_hard_practice_questions: {str(e)}")
            return []


# Global agent instance
search_agent = SearchAgent()
