"""
Enhanced DuckDuckGo search service with aggressive rate limiting and mock fallbacks.
"""

from duckduckgo_search import AsyncDDGS
from typing import List, Dict, Any, Optional
from loguru import logger
import asyncio
from datetime import datetime, timedelta
import hashlib
import random

from services.cache import cache_service
from config import settings


class MockSearchData:
    """Provides realistic fallback data when DuckDuckGo is unavailable."""
    
    EXAM_DATA = {
        "gate_it": {
            "syllabus": [
                {
                    "title": "GATE 2024 Information Technology Syllabus - Official",
                    "snippet": "Complete GATE IT syllabus covering Programming, Data Structures, Algorithms, Operating Systems, Database Management Systems, Computer Networks, Software Engineering, and Digital Logic.",
                    "url": "https://gate.iitm.ac.in/syllabus",
                    "source": "mock"
                },
                {
                    "title": "GATE IT Exam Pattern 2024 - Marks Distribution",
                    "snippet": "GATE IT exam consists of 65 questions for 100 marks. Section breakdown: General Aptitude (15 marks), Engineering Mathematics (13 marks), Core subjects (72 marks). Duration: 3 hours.",
                    "url": "https://gate.iitkgp.ac.in/pattern",
                    "source": "mock"
                }
            ],
            "resources": {
                "programming": [
                    {"title": "C Programming Complete Course - GeeksforGeeks", "snippet": "Learn C programming from basics to advanced", "url": "https://www.geeksforgeeks.org/c-programming-language/", "source": "mock"},
                    {"title": "Data Structures in C - TutorialsPoint", "snippet": "Comprehensive guide to data structures implementation", "url": "https://www.tutorialspoint.com/data_structures_algorithms/", "source": "mock"}
                ],
                "database": [
                    {"title": "DBMS Complete Tutorial - Javatpoint", "snippet": "Database Management Systems concepts with examples", "url": "https://www.javatpoint.com/dbms-tutorial", "source": "mock"},
                    {"title": "SQL Practice - W3Schools", "snippet": "Interactive SQL exercises and queries", "url": "https://www.w3schools.com/sql/", "source": "mock"}
                ]
            }
        },
        "jee_main": {
            "syllabus": [
                {
                    "title": "JEE Main 2024 Syllabus - Official NTA",
                    "snippet": "JEE Main syllabus for Physics, Chemistry, and Mathematics. Topics include Mechanics, Thermodynamics, Organic Chemistry, Inorganic Chemistry, Algebra, Calculus, and Coordinate Geometry.",
                    "url": "https://jeemain.nta.nic.in/syllabus",
                    "source": "mock"
                },
                {
                    "title": "JEE Main Exam Pattern - Marking Scheme",
                    "snippet": "JEE Main consists of 90 questions (30 each in Physics, Chemistry, Mathematics) for 300 marks. Each correct answer: +4 marks, incorrect: -1 mark. Duration: 3 hours.",
                    "url": "https://jeemain.nta.nic.in/pattern",
                    "source": "mock"
                }
            ],
            "resources": {
                "physics": [
                    {"title": "Physics Complete Course - Khan Academy", "snippet": "Free physics lectures covering mechanics, electricity, and modern physics", "url": "https://www.khanacademy.org/science/physics", "source": "mock"},
                    {"title": "HC Verma Solutions - Physics Concepts", "snippet": "Detailed solutions and concept explanations", "url": "https://www.vedantu.com/hc-verma-solutions", "source": "mock"}
                ],
                "chemistry": [
                    {"title": "Organic Chemistry - NCERT Solutions", "snippet": "Complete organic chemistry with reaction mechanisms", "url": "https://ncert.nic.in/chemistry", "source": "mock"},
                    {"title": "Chemical Reactions Practice - Toppr", "snippet": "Practice questions on chemical equations and stoichiometry", "url": "https://www.toppr.com/chemistry", "source": "mock"}
                ],
                "mathematics": [
                    {"title": "JEE Mathematics - Calculus and Algebra", "snippet": "Comprehensive math preparation with solved examples", "url": "https://www.mathongo.com/jee-mathematics", "source": "mock"},
                    {"title": "Coordinate Geometry Practice Problems", "snippet": "Advanced coordinate geometry for JEE preparation", "url": "https://brilliant.org/coordinate-geometry", "source": "mock"}
                ]
            }
        },
        "ielts": {
            "syllabus": [
                {
                    "title": "IELTS Exam Pattern 2024 - Academic and General Training",
                    "snippet": "IELTS consists of four sections: Listening (30 mins), Reading (60 mins), Writing (60 mins), and Speaking (11-14 mins). Total time: 2 hours and 45 minutes.",
                    "url": "https://www.ielts.org/about-the-test/test-format",
                    "source": "mock"
                },
                {
                    "title": "IELTS Syllabus and Scoring - Band Descriptors",
                    "snippet": "Detailed syllabus for Listening, Reading, Writing, and Speaking. Understanding the 1-9 band scale and assessment criteria.",
                    "url": "https://www.britishcouncil.in/exam/ielts/test-format",
                    "source": "mock"
                }
            ],
            "resources": {
                "listening": [
                    {"title": "IELTS Listening Practice Tests", "snippet": "Free online listening practice tests with audio and answers.", "url": "https://ielts-up.com/listening/ielts-listening-practice.html", "source": "mock"}
                ],
                "reading": [
                    {"title": "IELTS Reading Strategies - Academic", "snippet": "Tips for skimming, scanning, and identifying key information in IELTS reading.", "url": "https://www.ieltsbuddy.com/ielts-reading-tips.html", "source": "mock"}
                ],
                "writing": [
                    {"title": "IELTS Writing Task 1 & 2 - Model Answers", "snippet": "Sample essays and graph descriptions with expert feedback.", "url": "https://ieltsliz.com/ielts-writing-task-2/", "source": "mock"}
                ],
                "speaking": [
                    {"title": "IELTS Speaking Part 1, 2, 3 - Common Topics", "snippet": "Sample speaking questions and high-band model answers.", "url": "https://ieltsmaterial.com/speaking/", "source": "mock"}
                ]
            }
        }
    }
    
    @staticmethod
    def get_exam_results(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get mock results for exam-related queries."""
        query_lower = query.lower()
        
        # Detect exam type
        if "gate" in query_lower and ("it" in query_lower or "cs" in query_lower):
            exam_key = "gate_it"
        elif "jee" in query_lower:
            exam_key = "jee_main"
        elif "ielts" in query_lower:
            exam_key = "ielts"
        else:
            return MockSearchData.get_generic_results(query, max_results)
        
        exam_data = MockSearchData.EXAM_DATA.get(exam_key, {})
        
        # Return syllabus if query mentions syllabus
        if "syllabus" in query_lower or "pattern" in query_lower or "overview" in query_lower:
            results = exam_data.get("syllabus", [])
            logger.info(f"📚 Returning {len(results)} mock exam results for: {query}")
            return results[:max_results]
        
        # Return resources for specific subjects
        for subject, resources in exam_data.get("resources", {}).items():
            if subject in query_lower:
                logger.info(f"📖 Returning {len(resources)} mock resources for {subject}")
                return resources[:max_results]
        
        return MockSearchData.get_generic_results(query, max_results)
    
    @staticmethod
    def get_generic_results(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get generic mock results for any query."""
        
        # Extract topic from query using word-based replacement
        import re
        topic = query.lower()
        # Remove common search keywords but ONLY as whole words
        topic = re.sub(r'\b(tutorial|learn|study|best|resources|practice|videos)\b', '', topic).strip()
        # Clean up multiple spaces
        topic = re.sub(r'\s+', ' ', topic).title()
        
        if not topic:
            topic = "General Subject"
        
        generic_results = [
            {
                "title": f"{topic} - Complete Tutorial and Guide",
                "snippet": f"Comprehensive learning resources for {topic}. Includes theory, examples, and practice problems.",
                "url": f"https://www.geeksforgeeks.org/{topic.replace(' ', '-').lower()}",
                "source": "mock"
            },
            {
                "title": f"Learn {topic} - Free Online Course",
                "snippet": f"Free video lectures and tutorials on {topic}. Self-paced learning with quizzes and assignments.",
                "url": f"https://www.coursera.org/learn/{topic.replace(' ', '-').lower()}",
                "source": "mock"
            },
            {
                "title": f"{topic} Tutorial - Step by Step Guide",
                "snippet": f"Easy to follow tutorial covering {topic} from basics to advanced concepts with practical examples.",
                "url": f"https://www.tutorialspoint.com/{topic.replace(' ', '_').lower()}",
                "source": "mock"
            },
            {
                "title": f"{topic} - Video Lectures on YouTube",
                "snippet": f"Best YouTube channels for learning {topic}. Animated explanations and solved examples.",
                "url": f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}",
                "source": "mock"
            },
            {
                "title": f"Practice Problems - {topic}",
                "snippet": f"Solve practice problems and exercises on {topic}. Test your understanding with interactive quizzes.",
                "url": f"https://www.hackerrank.com/domains/{topic.replace(' ', '-').lower()}",
                "source": "mock"
            }
        ]
        
        logger.info(f"🎯 Returning {max_results} generic mock results for: {query}")
        return generic_results[:max_results]


class DuckDuckGoSearchService:
    """Enhanced service for DuckDuckGo web search with mock fallbacks."""
    
    def __init__(self):
        """Initialize DuckDuckGo search client."""
        self.ddgs = AsyncDDGS()
        # Ultra conservative rate limiting: 30-40 seconds between requests
        self.rate_limit_delay = 30.0
        self.last_request_time = None
        self._lock = asyncio.Lock()
        self._consecutive_failures = 0
        self._max_failures_before_fallback = 2  # Use mock after 2 failures
        self._fallback_mode = False
        self._fallback_until = None
    
    async def _rate_limit(self):
        """Implement aggressive rate limiting with random jitter."""
        if self.last_request_time:
            elapsed = (datetime.utcnow() - self.last_request_time).total_seconds()
            # Add random jitter: 30-40 seconds
            delay = self.rate_limit_delay + random.uniform(0, 10)
            if elapsed < delay:
                wait_time = delay - elapsed
                logger.debug(f"⏱️  Rate limiting: waiting {wait_time:.1f}s before next search...")
                await asyncio.sleep(wait_time)
        
        self.last_request_time = datetime.utcnow()
    
    def _generate_cache_key(self, query: str, max_results: int) -> str:
        """Generate cache key for search query."""
        content = f"{query}:{max_results}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _check_fallback_mode(self) -> bool:
        """Check if we should use fallback mode."""
        if self._fallback_until:
            if datetime.utcnow() < self._fallback_until:
                return True
            else:
                # Fallback period expired
                self._fallback_mode = False
                self._fallback_until = None
                self._consecutive_failures = 0
                logger.info("✅ Fallback mode deactivated - will try real search again")
        
        return self._fallback_mode
    
    def _activate_fallback_mode(self, duration_minutes: int = 15):
        """Activate fallback mode for specified duration."""
        self._fallback_mode = True
        self._fallback_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        logger.warning(
            f"⚠️  FALLBACK MODE ACTIVATED for {duration_minutes} minutes. "
            f"Using mock data until {self._fallback_until.strftime('%H:%M:%S')}"
        )
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        use_cache: bool = True,
        allow_fallback: bool = settings.duckduckgo_enable_fallback
    ) -> List[Dict[str, Any]]:
        """
        Perform web search with aggressive caching and mock fallbacks.
        
        Strategy:
        1. Check cache first
        2. If in fallback mode, use mock data
        3. Try real DuckDuckGo search with rate limiting
        4. On repeated failures, activate fallback mode
        """
        
        # Step 1: Check force mock mode
        if getattr(settings, 'force_mock_mode', False):
            logger.info(f"🔧 FORCE_MOCK_MODE: Using mock data for {query}")
            return MockSearchData.get_exam_results(query, max_results)

        # Step 2: Check cache
        if use_cache:
            cache_key = self._generate_cache_key(query, max_results)
            try:
                cached_results = await cache_service.get_search_results(cache_key)
                if cached_results:
                    logger.info(f"✅ Cache HIT for: {query}")
                    return cached_results
            except Exception as cache_err:
                logger.debug(f"Cache miss: {str(cache_err)}")
        
        # Step 2: Check if in fallback mode
        if allow_fallback and self._check_fallback_mode():
            logger.warning(f"🔄 Using fallback data (in fallback mode): {query}")
            return MockSearchData.get_exam_results(query, max_results)
        
        # Step 3: Try real search
        max_retries = 1  # Only 1 retry to avoid long waits
        
        async with self._lock:
            for attempt in range(max_retries + 1):
                try:
                    # Apply rate limiting
                    await self._rate_limit()
                    
                    logger.info(f"🔍 DuckDuckGo search (attempt {attempt+1}/{max_retries+1}): {query}")
                    
                    results = []
                    async with AsyncDDGS() as ddgs:
                        async for result in ddgs.text(query, max_results=max_results):
                            results.append({
                                "title": result.get("title", ""),
                                "snippet": result.get("body", ""),
                                "url": result.get("href", ""),
                                "source": "duckduckgo"
                            })
                    
                    if results:
                        logger.success(f"✅ Found {len(results)} real results for: {query}")
                        
                        # Reset failure counter on success
                        self._consecutive_failures = 0
                        
                        # Cache results
                        if use_cache:
                            try:
                                cache_key = self._generate_cache_key(query, max_results)
                                await cache_service.cache_search_results(cache_key, query, results)
                            except Exception:
                                pass
                        
                        return results
                    else:
                        logger.warning(f"⚠️  No results from DuckDuckGo for: {query}")
                
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    if "ratelimit" in error_msg or "429" in error_msg:
                        self._consecutive_failures += 1
                        logger.warning(
                            f"⚠️  Rate limit hit (attempt {attempt+1}, "
                            f"consecutive failures: {self._consecutive_failures}): {query}"
                        )
                        
                        if attempt < max_retries:
                            wait_time = 10  # Short wait for retry
                            logger.info(f"⏳ Waiting {wait_time}s before retry...")
                            await asyncio.sleep(wait_time)
                            continue
                        
                    else:
                        logger.error(f"❌ Search error: {str(e)}")
                        self._consecutive_failures += 1
        
        # Step 4: If we've failed multiple times, activate fallback mode
        if allow_fallback and self._consecutive_failures >= self._max_failures_before_fallback:
            self._activate_fallback_mode(duration_minutes=15)
            logger.warning(f"🔄 Using fallback data after {self._consecutive_failures} failures: {query}")
            return MockSearchData.get_exam_results(query, max_results)
        
        # Return empty if no fallback allowed
        logger.warning(f"⚠️  No results available for: {query}")
        return []
    
    async def search_exam_pattern(self, exam_name: str) -> List[Dict[str, Any]]:
        """Search for exam pattern and syllabus."""
        query = f"{exam_name} syllabus overview"
        return await self.search(query, max_results=5)
    
    async def search_topic_resources(
        self,
        topic: str,
        resource_type: str = "tutorial"
    ) -> List[Dict[str, Any]]:
        """Search for learning resources on a topic."""
        query = f"best {topic} learning resources {resource_type}s videos practice"
        return await self.search(query, max_results=8)
    
    async def search_previous_papers(
        self,
        exam_name: str,
        year: int = 2024
    ) -> List[Dict[str, Any]]:
        """Search for previous year question papers."""
        query = f"{exam_name} previous year papers {year}"
        return await self.search(query, max_results=8)
    
    async def deep_search(
        self,
        query: str,
        search_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Perform deep search with multiple queries."""
        max_results_map = {
            "basic": 5,
            "comprehensive": 8,
            "exhaustive": 12
        }
        
        max_results = max_results_map.get(search_depth, 8)
        
        # For deep search, only do main query to avoid rate limits
        main_results = await self.search(query, max_results=max_results)
        
        return {
            "query": query,
            "search_depth": search_depth,
            "main_results": main_results,
            "total_results": len(main_results),
            "timestamp": datetime.utcnow().isoformat(),
            "used_fallback": any(r.get("source") == "mock" for r in main_results)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of search service."""
        return {
            "fallback_mode": self._fallback_mode,
            "fallback_until": self._fallback_until.isoformat() if self._fallback_until else None,
            "consecutive_failures": self._consecutive_failures,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None
        }
    
    def force_enable_fallback(self, duration_minutes: int = 30):
        """Manually enable fallback mode."""
        self._activate_fallback_mode(duration_minutes)
    
    def force_disable_fallback(self):
        """Manually disable fallback mode."""
        self._fallback_mode = False
        self._fallback_until = None
        self._consecutive_failures = 0
        logger.info("✅ Fallback mode manually disabled")


# Global service instance
search_service = DuckDuckGoSearchService()
