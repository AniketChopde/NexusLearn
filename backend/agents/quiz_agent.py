"""
Quiz Agent for generating and evaluating quizzes.
"""

from typing import List, Dict, Any
from loguru import logger
import json
import re
from utils.helpers import parse_json_markdown, sanitize_jailbreak
import uuid

from services.azure_openai import azure_openai_service
from services.vector_store import vector_store_service
from agents.search_agent import search_agent

class QuizAgent:
    """Agent responsible for quiz generation from verified sources (Quiz Agent ROLE)."""
    
    def __init__(self):
        """Initialize Quiz Agent."""
        self.agent_name = "Quiz Agent"
        self.temperature = 0.4
    
    async def generate_questions(
        self,
        topic: str,
        module_id: str = None,
        count: int = 5,
        difficulty: str = "mixed", # Changed default to mixed for better assessment
        exam_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        ROLE: Quiz Agent
        TASK: Generate exam-level questions ONLY from retrieved module notes.
        """
        try:
            # 1. Retrieve context
            context = []
            if module_id:
                context = await vector_store_service.search(module_id, topic, top_k=6)
            
            # 2. Retrieve PYQs if exam type is specified
            pyq_context = []
            extracted_pyqs: List[Dict[str, Any]] = []
            pyq_sources: List[Dict[str, Any]] = []
            if exam_type:
                logger.info(f"Searching for {exam_type} PYQs for {topic}...")
                pyq_results = await search_agent.find_previous_year_questions(topic, exam_type)
                pyq_sources = [r for r in pyq_results if isinstance(r, dict)]
                extracted_pyqs = [r for r in pyq_results if isinstance(r, dict) and r.get("question")]

                if extracted_pyqs:
                    pyq_context = [
                        "\n".join(
                            [
                                f"PYQ QUESTION: {r.get('question', '')}",
                                f"EXAM: {r.get('exam')}",
                                f"YEAR: {r.get('year')}",
                                f"SOURCE_URL: {r.get('source_url')}",
                                f"SOURCE_TITLE: {r.get('source_title')}",
                            ]
                        )
                        for r in extracted_pyqs
                    ]
                else:
                    # Fallback to hard practice questions if no PYQs found
                    logger.info(f"No direct PYQs extracted for {topic}, searching for hard practice questions...")
                    practice_qs = await search_agent.find_hard_practice_questions(topic)
                    if practice_qs:
                        pyq_context = [
                            "\n".join(
                                [
                                    f"PRACTICE QUESTION: {r.get('question', '')}",
                                    f"OPTIONS: {', '.join(r.get('options', []))}",
                                    f"ANSWER: {r.get('answer')}",
                                    f"SOURCE_URL: {r.get('source_url')}",
                                ]
                            )
                            for r in practice_qs
                        ]

            context_text = ""
            if context or pyq_context:
                # Combine notes and PYQs
                notes_text = "\n\n".join([f"SOURCE: {c['source']}\nCONTENT: {c['text']}" for c in context])
                context_text = f"--- NOTES ---\n{notes_text}" if notes_text else ""

                if pyq_context:
                    pyq_text = "\n\n".join(pyq_context)
                    context_text = f"{context_text}\n\n--- PREVIOUS YEAR / PRACTICE QUESTIONS DATA ---\n{pyq_text}" if context_text else f"--- PREVIOUS YEAR / PRACTICE QUESTIONS DATA ---\n{pyq_text}"
                
            # Fallback prompt if no context is found (General Knowledge Quiz)
            if not context_text:
                logger.info(f"No specific context found for {topic}, generating general quiz.")
                system_prompt = f"""ROLE: Quiz Agent
                
                TASK:
                Generate {count} exam-level questions for the topic: {topic}.
                Since no specific notes are provided, use your general expert knowledge.
                
                QUESTION TYPES:
                - MCQ
                
                DIFFICULTY:
                Generate a mix of difficulty levels: Easy -> Medium -> Hard.
                
                OUTPUT SETTINGS:
                Return as JSON:
                {{
                  "questions": [
                    {{
                      "question": "The question text",
                      "options": ["A) Option Text 1", "B) Option Text 2", "C) Option Text 3", "D) Option Text 4"],
                      "correct_answer": "A",
                      "explanation": "Brief explanation",
                      "difficulty": "Easy/Medium/Hard",
                      "metadata": {{
                        "year": null,
                        "exam": null
                      }}
                    }}
                  ]
                }}
                IMPORTANT:
                - Options MUST start with "A) ", "B) ", "C) ", "D) ".
                - correct_answer MUST be just the letter "A", "B", "C", or "D".
                """
            else:
                # Grounded prompt
                system_prompt = f"""ROLE: Professional Quiz Generator
                
                TASK:
                Generate {count} objective questions based on the provided reference material and exam data.
                
                GUIDELINES:
                1. MATHEMATICAL ACCURACY: Verify all numerical values and calculations. Ensure the correct answer is available in the options.
                2. REFERENCE DATA: Prioritize content from the "REFERENCE MATERIAL" section.
                3. EVALUATION: Standard questions = 1 mark. Advanced/Previous Year questions = 4 marks.
                
                FORMATTING:
                Return ONLY a JSON object:
                {{
                  "questions": [
                    {{
                      "question": "Question text",
                      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
                      "correct_answer": "A",
                      "explanation": "Brief explanation or solution",
                      "difficulty": "Easy/Medium/Hard",
                      "marks": number,
                      "metadata": {{
                        "is_pyq": boolean,
                        "year": "YYYY",
                        "exam": "{exam_type or 'General'}"
                      }}
                    }}
                  ]
                }}
                
                REQUIREMENTS:
                - Options must start with "A) ", "B) ", "C) ", "D) ".
                - correct_answer must be a single letter ("A", "B", "C", or "D").
                """
            
            
            # 3. Sanitize context to prevent Jailbreak triggers
            clean_context_text = sanitize_jailbreak(context_text)

            user_prompt = f"""
            Topic: {topic}
            Target Exam: {exam_type or "General"}
            
            REFERENCE MATERIAL:
            {clean_context_text}
            
            Instruction: Generate {count} questions based on the above material.
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )
            
            result = parse_json_markdown(response)
            questions = result.get("questions", [])

            # If we have extracted literal PYQs but the model didn't include enough, materialize PYQs explicitly.
            # IMPORTANT: Do NOT generate "PYQ-style" questions from snippets when extraction fails.
            if exam_type and extracted_pyqs:
                pyq_count = sum(1 for q in questions if q.get("metadata", {}).get("is_pyq"))
                target_pyq_total = min(2, len(extracted_pyqs))
                if pyq_count < target_pyq_total:
                    needed = target_pyq_total - pyq_count

                    def infer_year(text: str):
                        match = re.search(r"\b(20\d{2})\b", text or "")
                        if match:
                            return match.group(1)
                        return None

                    targets = extracted_pyqs[:needed]

                    system_prompt_pyq = """You convert extracted Previous Year Questions (PYQs) into MCQs.

Return JSON:
{
  "questions": [
    {
      "question": "<use the provided PYQ question text>",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_answer": "A",
      "explanation": "Detailed step-by-step solution",
      "difficulty": "Hard",
      "marks": 4,
      "metadata": {
        "is_pyq": true,
        "exam": "<exam name>",
        "year": "<YYYY or null>",
        "source_url": "<url>",
        "source_title": "<title>"
      }
    }
  ]
}

Rules:
- If a literal PYQ question text is provided, keep it the same.
- Options must be plausible and one must be correct.
- correct_answer must be only the letter.
"""

                    user_prompt_pyq = f"""
Target Exam: {exam_type}
Topic: {topic}

PYQ QUESTION INPUTS (may include literal questions):
{json.dumps(targets, indent=2)}
"""

                    try:
                        pyq_resp = await azure_openai_service.generate_structured_output(
                            system_prompt=system_prompt_pyq,
                            user_prompt=user_prompt_pyq,
                            temperature=self.temperature
                        )
                        pyq_parsed = parse_json_markdown(pyq_resp)
                        pyq_questions = pyq_parsed.get("questions", []) if isinstance(pyq_parsed, dict) else []
                        pyq_questions = [q for q in pyq_questions if isinstance(q, dict) and q.get("question")]

                        if pyq_questions:
                            if len(questions) >= len(pyq_questions):
                                questions[-len(pyq_questions):] = pyq_questions
                            else:
                                questions.extend(pyq_questions)

                            # Keep within requested count
                            if len(questions) > count:
                                questions = questions[:count]
                    except Exception:
                        pass
            
            # Post-processing to ensure format
            for q in questions:
                # Ensure options have prefixes
                prefixes = ["A) ", "B) ", "C) ", "D) "]
                new_options = []
                for idx, opt in enumerate(q.get("options", [])):
                    if idx < 4:
                        # Clean existing prefix if messy
                        clean_opt = opt
                        if opt.startswith(prefixes[idx]):
                             pass
                        elif opt[0] in ['A', 'B', 'C', 'D'] and opt[1] in [')', '.']:
                             clean_opt = opt[3:].strip()
                             clean_opt = prefixes[idx] + clean_opt
                        else:
                             clean_opt = prefixes[idx] + opt
                        new_options.append(clean_opt)
                q["options"] = new_options

                # Ensure correct_answer is a letter
                ca = q.get("correct_answer", "").strip()
                if len(ca) > 1:
                    # If AI put full text as answer, find which option creates it
                    # OR if it starts with "A)"
                    if ca.startswith("A") and (len(ca)==1 or ca[1] in [')', '.']): q["correct_answer"] = "A"
                    elif ca.startswith("B") and (len(ca)==1 or ca[1] in [')', '.']): q["correct_answer"] = "B"
                    elif ca.startswith("C") and (len(ca)==1 or ca[1] in [')', '.']): q["correct_answer"] = "C"
                    elif ca.startswith("D") and (len(ca)==1 or ca[1] in [')', '.']): q["correct_answer"] = "D"
            
            # Add unique IDs
            for q in questions:
                q["question_id"] = str(uuid.uuid4())
                q["topic"] = topic
                q["topic"] = topic
                q["difficulty"] = q.get("difficulty", difficulty)
                
                # Default marks if missing
                if "marks" not in q:
                    q["marks"] = 4 if q.get("metadata", {}).get("is_pyq") else 1

                # Ensure metadata exists
                if "metadata" not in q:
                    q["metadata"] = {"is_pyq": False, "exam": exam_type}

                # If we failed to extract real PYQs from the web, never label anything as a PYQ.
                if exam_type and not extracted_pyqs:
                    if not isinstance(q.get("metadata"), dict):
                        q["metadata"] = {"is_pyq": False, "exam": exam_type}
                    q["metadata"]["is_pyq"] = False
                    q["marks"] = 1
            
            logger.info(f"Quiz Agent generated {len(questions)} grounded questions for: {topic}")
            return questions
        
        except Exception as e:
            logger.error(f"Error in Quiz Agent (generate_questions): {str(e)}")
            raise

    
    async def evaluate_answer(
        self,
        question: Dict[str, Any],
        user_answer: str
    ) -> Dict[str, Any]:
        """
        Evaluate a user's answer to a question.
        
        Args:
            question: Question dictionary
            user_answer: User's answer
        
        Returns:
            Evaluation result
        """
        try:
            correct_answer = question.get("correct_answer", "").strip()
            user_answer = user_answer.strip().upper()
            is_correct = user_answer == correct_answer.upper()
            
            # Fallback: If not direct match, check if correct_answer is content of the option letter
            if not is_correct and len(user_answer) == 1 and user_answer in ['A', 'B', 'C', 'D']:
                try:
                    idx = ord(user_answer) - 65 # A=0, B=1...
                    options = question.get("options", [])
                    if idx < len(options):
                        opt_text = options[idx]
                        # If correct_answer (e.g. "25%") is inside the option text (e.g. "B) 25%")
                        if correct_answer.lower() in opt_text.lower():
                            is_correct = True
                        # Or if correct_answer matches the letter prefix of option
                        if opt_text.upper().startswith(f"{correct_answer.upper()})"):
                             is_correct = True
                except Exception:
                    pass
            
            evaluation = {
                "question_id": question.get("question_id"),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
                "marks_obtained": question.get("marks", 1) if is_correct else 0,
                "total_marks": question.get("marks", 1)
            }
            
            return evaluation
        
        except Exception as e:
            logger.error(f"Error in evaluate_answer: {str(e)}")
            raise
    
    async def calculate_score(
        self,
        quiz_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall quiz score and analytics.
        
        Args:
            quiz_session: Quiz session with questions and answers
        
        Returns:
            Score and analytics
        """
        try:
            questions = quiz_session.get("questions", [])
            answers = quiz_session.get("answers", {})
            
            total_questions = len(questions)
            correct_answers = 0
            total_marks = 0
            obtained_marks = 0
            
            detailed_results = []
            
            for question in questions:
                question_id = question.get("question_id")
                user_answer = answers.get(question_id, "")
                
                evaluation = await self.evaluate_answer(question, user_answer)
                detailed_results.append(evaluation)
                
                total_marks += evaluation["total_marks"]
                obtained_marks += evaluation["marks_obtained"]
                
                if evaluation["is_correct"]:
                    correct_answers += 1
            
            percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
            
            score_data = {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "incorrect_answers": total_questions - correct_answers,
                "total_marks": total_marks,
                "obtained_marks": obtained_marks,
                "percentage": round(percentage, 2),
                "grade": self._get_grade(percentage),
                "detailed_results": detailed_results
            }
            
            logger.info(f"Quiz score calculated: {percentage}%")
            return score_data
        
        except Exception as e:
            logger.error(f"Error in calculate_score: {str(e)}")
            raise
    
    def _get_grade(self, percentage: float) -> str:
        """Get grade based on percentage."""
        if percentage >= 90:
            return "A+"
        elif percentage >= 80:
            return "A"
        elif percentage >= 70:
            return "B+"
        elif percentage >= 60:
            return "B"
        elif percentage >= 50:
            return "C"
        else:
            return "F"
    
    async def generate_adaptive_questions(
        self,
        topic: str,
        previous_performance: List[Dict[str, Any]],
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate adaptive questions based on previous performance.
        
        Args:
            topic: Topic for questions
            previous_performance: Previous quiz results
            count: Number of questions
        
        Returns:
            Adaptive questions
        """
        try:
            # Analyze performance to determine difficulty
            if not previous_performance:
                difficulty = "medium"
            else:
                avg_score = sum(
                    p.get("percentage", 0) for p in previous_performance
                ) / len(previous_performance)
                
                if avg_score >= 80:
                    difficulty = "hard"
                elif avg_score >= 50:
                    difficulty = "medium"
                else:
                    difficulty = "easy"
            
            # Identify weak areas
            weak_subtopics = []
            for perf in previous_performance:
                for result in perf.get("detailed_results", []):
                    if not result.get("is_correct"):
                        weak_subtopics.append(result.get("topic", topic))
            
            system_prompt = f"""Generate {count} adaptive questions focusing on weak areas.
            
            Difficulty: {difficulty}
            Weak Areas: {', '.join(set(weak_subtopics)) if weak_subtopics else 'None identified'}
            
            Return as JSON with structure matching generate_questions."""
            
            user_prompt = f"""
            Topic: {topic}
            Previous Performance: {json.dumps(previous_performance[-3:], indent=2)}
            
            Generate adaptive questions targeting weak areas.
            """
            
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            
            result = parse_json_markdown(response)
            questions = result.get("questions", [])
            
            logger.info(f"Generated {len(questions)} adaptive questions")
            return questions
        
        except Exception as e:
            logger.error(f"Error in generate_adaptive_questions: {str(e)}")
            raise
    
    async def generate_test_center_questions(
        self,
        topic: str,
        count: int,
        exam_type: str,
        skip_pyq: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Fast quiz generation for Test Center. One LLM call; set skip_pyq=True for under-10s path.
        """
        try:
            logger.info(f"⚡ Fast Test Center: {count} questions for {topic} (skip_pyq={skip_pyq})")
            pyq_summary = ""
            pyq_found = False
            if exam_type and not skip_pyq:
                try:
                    pyq_results = await search_agent.find_previous_year_questions(topic, exam_type)
                    extracted_pyqs = [r for r in pyq_results if isinstance(r, dict) and r.get("question")]
                    if extracted_pyqs:
                        sample_pyqs = extracted_pyqs[:3]
                        pyq_summary = "\n".join([
                            f"- {p.get('question', '')[:150]}... (Year: {p.get('year', 'N/A')})"
                            for p in sample_pyqs
                        ])
                        pyq_found = True
                except Exception as e:
                    logger.warning(f"PYQ search failed: {e}, continuing without PYQs")
            # Short prompt for low latency
            system_prompt = f"""Generate {count} exam-level MCQ questions for {exam_type}.

REQUIREMENTS:
- Mix difficulty: Easy (30%), Medium (40%), Hard (30%)
- All questions MUST have exactly 4 options
- Options prefix: "A) ", "B) ", "C) ", "D) "
-correct_answer: Single letter only ("A", "B", "C", or "D")

JSON FORMAT:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_answer": "A",
      "explanation": "Brief solution",
      "difficulty": "Easy/Medium/Hard",
      "marks": 1,
      "metadata": {{"is_pyq": false, "exam": "{exam_type}"}}
    }}
  ]
}}"""

            # Fix SyntaxError: Extract pyq_section to avoid backslash in f-expression
            pyq_section = f"""PYQ Examples (for reference):
{pyq_summary}""" if pyq_found else ""

            # Minimal user prompt
            user_prompt = f"""Topic: {topic}
Exam: {exam_type}
Count: {count} questions

{pyq_section}

Generate {count} high-quality exam questions."""

            # Single LLM call for all questions
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5  # Balanced creativity
            )
            
            result = parse_json_markdown(response)
            questions = result.get("questions", [])
            
            # Post-processing (same as original)
            for q in questions:
                # Ensure options have prefixes
                prefixes = ["A) ", "B) ", "C) ", "D) "]
                new_options = []
                for idx, opt in enumerate(q.get("options", [])):
                    if idx < 4:
                        clean_opt = opt
                        if not opt.startswith(prefixes[idx]):
                            if opt[0] in ['A', 'B', 'C', 'D'] and opt[1] in [')', '.']:
                                clean_opt = prefixes[idx] + opt[3:].strip()
                            else:
                                clean_opt = prefixes[idx] + opt
                        new_options.append(clean_opt)
                q["options"] = new_options
                
                # Ensure correct_answer is a letter
                ca = q.get("correct_answer", "").strip()
                if len(ca) > 1:
                    if ca.startswith("A"): q["correct_answer"] = "A"
                    elif ca.startswith("B"): q["correct_answer"] = "B"
                    elif ca.startswith("C"): q["correct_answer"] = "C"
                    elif ca.startswith("D"): q["correct_answer"] = "D"
                
                # Add metadata
                q["question_id"] = str(uuid.uuid4())
                q["topic"] = topic
                q.setdefault("marks", 1)
                q.setdefault("difficulty", "Medium")
                q.setdefault("metadata", {"is_pyq": False, "exam": exam_type})
            
            logger.info(f"⚡ Fast generated {len(questions)} questions for Test Center")
            return questions[:count]  # Ensure exact count
            
        except Exception as e:
            logger.error(f"❌ Error in generate_test_center_questions: {str(e)}")
            raise



    async def generate_chapter_questions(
        self,
        topics: List[str],
        exam_type: str,
        total_count: int = 15
    ) -> List[Dict[str, Any]]:
        """
        ULTRA-OPTIMIZED: Generate high-quality questions for multiple chapter topics.
        Batches searches and LLM generation for maximum speed.
        """
        try:
            logger.info(f"⚡ Batch generating {total_count} chapter questions for: {topics}")
            
            # 1. Batched PYQ Search (Only 2 high-power searches for the whole sub-set)
            search_query = f"{exam_type} {' '.join(topics[:3])} previous year questions with solutions pyq"
            logger.info(f"🔍 Batched PYQ Search: {search_query}")
            
            pyq_results = await search_agent.find_previous_year_questions(search_query, exam_type)
            extracted_pyqs = [r for r in pyq_results if isinstance(r, dict) and r.get("question")]
            
            sample_pyqs = extracted_pyqs[:5]
            pyq_context = "\n".join([
                f"- QUESTION: {p.get('question', '')[:200]}\n  EXAM: {p.get('exam')} {p.get('year', '')}"
                for p in sample_pyqs
            ]) if sample_pyqs else "None found."
            
            # 2. Optimized Prompt for Multiple Topics
            system_prompt = f"""Generate {total_count} official-level MCQ questions for {exam_type}.
            
            TOPICS TO COVER: {', '.join(topics)}
            
            REQUIREMENTS:
            - Distribute questions evenly across the provided topics.
            - Mix difficulty: Medium to Hard.
            - Exactly 4 options per question, prefixed with "A) ", "B) ", "C) ", "D) ".
            - correct_answer: SINGLE LETTER ("A", "B", "C", or "D").
            
            OUTPUT JSON:
            {{
              "questions": [
                {{
                  "question": "...",
                  "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
                  "correct_answer": "A",
                  "explanation": "...",
                  "difficulty": "Medium/Hard",
                  "topic": "Selected from input topics",
                  "metadata": {{"is_pyq": boolean, "exam": "{exam_type}"}}
                }}
              ]
            }}"""
            
            user_prompt = f"""Generate {total_count} questions covering: {topics}.
            Exam: {exam_type}
            
            PYQ EXAMPLES FOR STYLE REFERENCE:
            {pyq_context}
            """
            
            # 3. Single LLM Call for the whole chapter
            response = await azure_openai_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4
            )
            
            result = parse_json_markdown(response)
            questions = result.get("questions", [])
            
            # Post-processing
            for q in questions:
                q["question_id"] = str(uuid.uuid4())
                if "topic" not in q: q["topic"] = topics[0]
                q.setdefault("marks", 4 if q.get("metadata", {}).get("is_pyq") else 1)
                
            logger.info(f"✅ Batch generated {len(questions)} questions")
            return questions[:total_count]
            
        except Exception as e:
            logger.error(f"Error in batch generation: {e}")
            # Fallback to simple generation if complex one fails
            return await self.generate_questions(topic=" ".join(topics), count=total_count, exam_type=exam_type)

# Global agent instance
quiz_agent = QuizAgent()
