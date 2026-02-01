from typing import Dict, Any, List
from loguru import logger

class SafetyAgent:
    """Agent responsible for checking context grounding and relevance (Grounding Guard ROLE)."""
    
    def __init__(self):
        self.agent_name = "Grounding Guard"
        self.context_threshold = 200
        self.min_chunks = 2
        self.min_similarity_score = 0.15

    async def check_grounding(self, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        TASK:
        Check retrieved context length & relevance.
        RULE:
        If context < threshold:
        - Block answer
        - Ask user to revise previous module
        """
        total_length = sum(len(c.get("text", "")) for c in context)
        chunk_count = len(context)
        best_score = None
        for c in context:
            score = c.get("similarity_score")
            if isinstance(score, (int, float)):
                best_score = score if best_score is None else max(best_score, score)

        if chunk_count < self.min_chunks:
            logger.warning(f"Safety Agent BLOCKED: Retrieved chunk_count {chunk_count} is below min_chunks {self.min_chunks}")
            return {
                "allowed": False,
                "message": "Grounding check failed: Not enough verified context was retrieved from your indexed sources. Please revise previous modules or fetch sources for this topic.",
                "action": "BLOCK"
            }

        if total_length < self.context_threshold:
            logger.warning(f"Safety Agent BLOCKED: Combined context length {total_length} is below threshold {self.context_threshold}")
            return {
                "allowed": False,
                "message": "Grounding check failed: Insufficient verified context found in your indexed sources. Please revise previous modules or fetch sources for this topic.",
                "action": "BLOCK"
            }

        if best_score is not None and best_score < self.min_similarity_score:
            logger.warning(f"Safety Agent BLOCKED: best_similarity_score {best_score} is below min_similarity_score {self.min_similarity_score}")
            return {
                "allowed": False,
                "message": "Grounding check failed: Retrieved sources are not sufficiently relevant to answer confidently. Please refine your question or study prerequisite topics.",
                "action": "BLOCK"
            }
        
        return {
            "allowed": True,
            "message": "Grounding check passed.",
            "action": "ALLOW"
        }

safety_agent = SafetyAgent()
