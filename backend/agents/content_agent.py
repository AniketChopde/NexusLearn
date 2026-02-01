"""
Content Agent for generating detailed explanations and learning materials.
"""

from typing import List, Dict, Any
from loguru import logger
from utils.helpers import parse_json_markdown

from services.azure_openai import azure_openai_service
from services.vector_store import vector_store_service
from agents.safety_agent import safety_agent

class ContentAgent:
    """Agent responsible for source-grounded teaching (Teaching Agent ROLE)."""
    
    def __init__(self):
        """Initialize Content Agent."""
        self.agent_name = "Teaching Agent"
        self.temperature = 0.2
    
    async def explain_concept(
        self,
        module_id: str,
        topic: str,
        module_name: str = "Specific Module",
        user_question: str = None
    ) -> Dict[str, Any]:
        """
        ROLE: Teaching Agent
        RULES:
        - Answer ONLY using retrieved clean_notes
        - Cite source_domain in every response
        - Use simple language based on user level
        - If answer is not found, say: "This is outside the current syllabus."
        """
        try:
            # 1. Retrieve context from FAISS
            context = await vector_store_service.search(module_id, user_question or topic)
            
            # 2. Safety Check
            safety_check = await safety_agent.check_grounding(context)
            if not safety_check["allowed"]:
                return {
                    "topic": topic,
                    "main_explanation": safety_check["message"],
                    "is_blocked": True,
                    "citation": "Safety Filter"
                }

            # 3. Format context
            context_text = "\n\n".join([
                f"SOURCE: {c['source']}\nCONTENT: {c['text']}"
                for c in context
            ])
            
            system_prompt = f"""ROLE: Teaching Agent
            
            RULES:
            - Answer ONLY using the retrieved clean_notes below.
            - Cite the source_domain (e.g., [ncert.nic.in]) in every response.
            - Use simple, clear language.
            - If the answer is NOT in the context, say: "This information is outside the current syllabus current source material."
            - Do NOT use internal knowledge or internet beyond the provided context.
            
            STRICT FORMATTING:
            Return as JSON:
            {{
                "topic": "{topic}",
                "introduction": "Brief intro",
                "main_explanation": "The core explanation with citations [domain]",
                "key_points": ["point1", "point2"],
                "citation": "Primary source domain",
                "visual_description": "A textual description of the visual",
                "mermaid_diagram": "Mermaid code starting with graph TD or sequenceDiagram or classDiagram to visualize the concept"
            }}
            """
            
            user_prompt = f"""
            Module: {module_name}
            Question/Topic: {user_question or topic}
            
            RETRIEVED CONTEXT:
            {context_text}
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )
            
            explanation = parse_json_markdown(response)
            logger.info(f"Teaching Agent generated grounded explanation for: {topic}")
            return explanation
        
        except Exception as e:
            logger.error(f"Error in Teaching Agent (explain_concept): {str(e)}")
            raise

    
    async def explain_concept_fast(
        self,
        topic: str,
        exam_type: str = "General",
        context: str = None
    ) -> Dict[str, Any]:
        """
        FAST PATH: Generate explanation directly from LLM without RAG.
        Used for "deep lesson" to reduce latency from 5 min to 30 sec.
        
        Args:
            topic: Topic to explain
            exam_type: Exam context (GATE_IT, JEE, NEET, etc.)
            context: Additional context (chapter name, etc.)
        
        Returns:
            Explanation with key points and examples
        """
        try:
            logger.info(f"⚡ Fast explanation (no RAG) for: {topic}")
            
            system_prompt = f"""You are an expert educator preparing students for {exam_type} exams.
            
            Generate a comprehensive, well-structured explanation for the given topic.
            
            RULES:
            - Use clear, simple language suitable for students
            - Include concrete examples with code where applicable
            - Focus on exam-relevant content
            - Structure the explanation logically
            - Create a visual/conceptual diagram description
            - Generate a Mermaid diagram to visualize the concept
            
            Return as JSON:
            {{
                "topic": "{topic}",
                "introduction": "Brief 2-3 sentence introduction to the topic",
                "main_explanation": "Comprehensive detailed explanation covering all key aspects. Use paragraphs and clear structure. This should be the MAIN content (200-400 words).",
                "key_points": [
                    "Key point 1 with details",
                    "Key point 2 with details", 
                    "Key point 3 with details",
                    "Key point 4 with details"
                ],
                "examples": [
                    {{
                        "title": "Example 1 name",
                        "description": "Detailed explanation with code if applicable",
                        "code": "// Code snippet if applicable"
                    }},
                    {{
                        "title": "Example 2 name", 
                        "description": "Another practical example"
                    }}
                ],
                "common_mistakes": [
                    "Common mistake 1 and how to avoid it",
                    "Common mistake 2 and how to avoid it"
                ],
                "exam_tips": [
                    "Tip 1 for exam preparation",
                    "Tip 2 for scoring well"
                ],
                "visual_description": "A detailed textual description of how this concept can be visualized (e.g., flowchart, diagram, memory layout, etc.)",
                "mermaid_diagram": "graph TD\\n    A[Start] --> B[Step 1]\\n    B --> C[Step 2]\\n    C --> D[End]\\n    %% Create a proper Mermaid diagram (graph TD, flowchart, sequenceDiagram, or classDiagram) that visualizes the concept"
            }}
            
            IMPORTANT: 
            - main_explanation must be comprehensive (200-400 words)
            - mermaid_diagram must be valid Mermaid syntax starting with graph TD, flowchart, sequenceDiagram, or classDiagram
            - Include at least 2 detailed examples
            """
            
            user_prompt = f"""
            Exam Type: {exam_type}
            {f'Context: {context}' if context else ''}
            Topic: {topic}
            
            Provide a detailed, comprehensive explanation suitable for exam preparation.
            Focus on clarity, practical examples, and visual representation.
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3  # Lower for more focused explanations
            )
            
            explanation = parse_json_markdown(response)
            logger.info(f"✅ Fast explanation generated for: {topic}")
            return explanation
        
        except Exception as e:
            logger.error(f"❌ Error in explain_concept_fast: {str(e)}")
            raise


    async def generate_examples(
        self,
        topic: str,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate practical examples for a topic.
        
        Args:
            topic: Topic for examples
            count: Number of examples to generate
        
        Returns:
            List of examples
        """
        try:
            system_prompt = f"""Generate {count} practical examples for the given topic.
            
            Return as JSON: {{
                "examples": [
                    {{
                        "title": "example title",
                        "scenario": "real-world scenario",
                        "solution": "step-by-step solution",
                        "code": "code if applicable",
                        "explanation": "why this works"
                    }}
                ]
            }}"""
            
            user_prompt = f"Topic: {topic}\n\nGenerate {count} diverse, practical examples."
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            
            result = parse_json_markdown(response)
            logger.info(f"Generated {count} examples for: {topic}")
            return result.get("examples", [])
        
        except Exception as e:
            logger.error(f"Error in generate_examples: {str(e)}")
            return []
    
    async def create_practical_exercises(
        self,
        topic: str,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create practical exercises for a topic.
        
        Args:
            topic: Topic for exercises
            difficulty: Difficulty level
        
        Returns:
            Set of exercises
        """
        try:
            system_prompt = f"""Create practical exercises for the given topic at {difficulty} difficulty.
            
            Return as JSON: {{
                "exercises": [
                    {{
                        "exercise_number": 1,
                        "title": "exercise title",
                        "description": "what to do",
                        "hints": ["hint1", "hint2"],
                        "solution_approach": "how to solve",
                        "expected_outcome": "what should be achieved"
                    }}
                ],
                "learning_objectives": ["objective1", "objective2"]
            }}"""
            
            user_prompt = f"Topic: {topic}\nDifficulty: {difficulty}"
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.6
            )
            
            exercises = parse_json_markdown(response)
            logger.info(f"Created exercises for: {topic}")
            return exercises
        
        except Exception as e:
            logger.error(f"Error in create_practical_exercises: {str(e)}")
            raise
    
    async def generate_chapter_breakdown(
        self,
        chapter_name: str,
        topics: List[str]
    ) -> Dict[str, Any]:
        """
        Generate detailed content breakdown for a chapter.
        
        Args:
            chapter_name: Name of the chapter
            topics: List of topics in the chapter
        
        Returns:
            Detailed chapter content structure
        """
        try:
            system_prompt = """Create a detailed content structure for the chapter.
            
            Return as JSON: {
                "chapter_overview": "brief overview",
                "learning_path": [
                    {
                        "step": 1,
                        "topic": "topic name",
                        "description": "what to learn",
                        "estimated_time_minutes": number,
                        "resources_needed": ["resource1", "resource2"]
                    }
                ],
                "key_takeaways": ["takeaway1", "takeaway2"],
                "assessment_criteria": ["criteria1", "criteria2"]
            }"""
            
            user_prompt = f"""
            Chapter: {chapter_name}
            Topics: {', '.join(topics)}
            
            Create a structured learning path for this chapter.
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5
            )
            
            breakdown = parse_json_markdown(response)
            logger.info(f"Chapter breakdown generated for: {chapter_name}")
            return breakdown
        
        except Exception as e:
            logger.error(f"Error in generate_chapter_breakdown: {str(e)}")
            raise
    
    async def create_mindmap(self, subject: str) -> Dict[str, Any]:
        """
        Create a mindmap structure for a subject.
        
        Args:
            subject: Subject name
        
        Returns:
            Mindmap structure
        """
        try:
            system_prompt = """Create a hierarchical mindmap structure for the subject.
            
            Return as JSON: {
                "central_topic": "subject name",
                "main_branches": [
                    {
                        "branch_name": "branch",
                        "sub_branches": [
                            {
                                "name": "sub-branch",
                                "concepts": ["concept1", "concept2"]
                            }
                        ]
                    }
                ],
                "connections": [
                    {
                        "from": "topic1",
                        "to": "topic2",
                        "relationship": "relationship type"
                    }
                ]
            }"""
            
            user_prompt = f"Subject: {subject}\n\nCreate a comprehensive mindmap."
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4
            )
            
            mindmap = parse_json_markdown(response)
            logger.info(f"Mindmap created for: {subject}")
            return mindmap
        
        except Exception as e:
            logger.error(f"Error in create_mindmap: {str(e)}")
            raise


# Global agent instance
content_agent = ContentAgent()
