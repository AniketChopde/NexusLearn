"""
SerpApi search service for high-quality, reliable internet searches.
"""

import httpx
from typing import List, Dict, Any, Optional
from loguru import logger
import asyncio
import hashlib
from datetime import datetime

from config import settings
from services.cache import cache_service

class SerpApiSearchService:
    """Service for performing web searches via SerpApi."""
    
    def __init__(self):
        """Initialize SerpApi service."""
        self.api_key = settings.serpapi_api_key
        self.base_url = "https://serpapi.com/search.json"
        self._lock = asyncio.Lock()
    
    def _generate_cache_key(self, query: str, max_results: int) -> str:
        """Generate cache key for search query."""
        content = f"serpapi:{query}:{max_results}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def search(
        self,
        query: str,
        engine: str = "google",
        max_results: int = 10,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform web search using SerpApi.
        """
        # Step 1: Check cache
        if use_cache:
            cache_key = self._generate_cache_key(query, max_results)
            try:
                cached_results = await cache_service.get_search_results(cache_key)
                if cached_results:
                    logger.info(f"✅ SerpApi Cache HIT for: {query}")
                    return cached_results
            except Exception:
                pass

        # Check for API key
        if not self.api_key or self.api_key == "your-serpapi-key-here":
            logger.error("❌ SerpApi API Key is MISSING. Please configure SERPAPI_API_KEY in .env")
            raise ValueError("SerpApi Key not configured")

        # Step 2: Call SerpApi
        params = {
            "q": query,
            "engine": engine,
            "api_key": self.api_key,
            "num": max_results
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"🔍 SerpApi search using {engine}: {query}")
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    # Process organic results
                    organic_results = data.get("organic_results", [])
                    for result in organic_results[:max_results]:
                        results.append({
                            "title": result.get("title", ""),
                            "snippet": result.get("snippet", ""),
                            "url": result.get("link", ""),
                            "source": f"serpapi_{engine}"
                        })
                    
                    if results:
                        logger.success(f"✅ SerpApi found {len(results)} results for: {query}")
                        # Cache results
                        if use_cache:
                            cache_key = self._generate_cache_key(query, max_results)
                            await cache_service.cache_search_results(cache_key, query, results)
                        return results
                    else:
                        logger.warning(f"⚠️ SerpApi returned no results for: {query}")
                        return []
                    
                else:
                    logger.error(f"❌ SerpApi error {response.status_code}: {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ SerpApi unexpected error: {str(e)}")
            return []

    async def deep_search(self, query: str, depth: str = "standard") -> Dict[str, Any]:
        """
        Perform deep search with multi-engine support.
        """
        results = await self.search(query, max_results=10)
        return {
            "query": query,
            "main_results": results,
            "related_results": [],
            "search_metadata": {
                "engine": "google",
                "depth": depth,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    async def search_exam_pattern(self, exam_name: str) -> List[Dict[str, Any]]:
        """Search for exam pattern and syllabus."""
        query = f"{exam_name} exam pattern total questions marks distribution per subject"
        return await self.search(query, max_results=8)
    
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
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of search service."""
        return {
            "active_engine": "serpapi",
            "api_configured": bool(self.api_key and self.api_key != "your-serpapi-key-here"),
            "timestamp": datetime.utcnow().isoformat()
        }

# Global service instance
serpapi_service = SerpApiSearchService()
