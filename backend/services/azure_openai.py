"""
Azure OpenAI service for LLM interactions.
"""

from fastapi import HTTPException
from openai import AsyncAzureOpenAI
from typing import List, Dict, Any, Optional
from loguru import logger
import tiktoken

from config import settings


class AzureOpenAIService:
    """Service for interacting with Azure OpenAI."""
    
    def __init__(self):
        """Initialize Azure OpenAI clients (separate for chat and embeddings)."""
        # Chat/LLM client
        self.client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_key,
            api_version=settings.azure_openai_api_version,
        )
        self.deployment = settings.azure_openai_deployment
        
        # Embedding client (may use different endpoint/key)
        self.embedding_client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_embedding_endpoint,
            api_key=settings.azure_openai_embedding_key,
            api_version=settings.azure_openai_api_version,
        )
        self.embedding_deployment = settings.azure_openai_embedding_deployment
        
        self.encoding = tiktoken.encoding_for_model("gpt-4")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, str]] = None,
        return_full_response: bool = False
    ) -> Any:
        """
        Generate chat completion.
        """
        try:
            kwargs = {
                "model": self.deployment,
                "messages": messages,
                "temperature": temperature,
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            logger.debug(f"Attempting Azure OpenAI chat completion at {settings.azure_openai_endpoint}")
            
            # Try with max_completion_tokens first (GPT-5.x models)
            try:
                kwargs["max_completion_tokens"] = max_tokens
                response = await self.client.chat.completions.create(**kwargs)
            except (TypeError, Exception) as e:
                error_msg = str(e)
                
                # Check if it's a parameter compatibility issue
                if "max_completion_tokens" in error_msg and ("not supported" in error_msg or "unexpected keyword" in error_msg):
                    # Library doesn't support max_completion_tokens, try max_tokens
                    logger.debug("max_completion_tokens not supported, trying max_tokens")
                    kwargs.pop("max_completion_tokens", None)
                    kwargs["max_tokens"] = max_tokens
                    try:
                        response = await self.client.chat.completions.create(**kwargs)
                    except Exception as e2:
                        error_msg2 = str(e2)
                        # Check for temperature restrictions
                        if "temperature" in error_msg2 and ("not support" in error_msg2 or "only the default" in error_msg2.lower()):
                            logger.warning(f"Temperature {kwargs.get('temperature')} not supported, using default temperature=1")
                            kwargs["temperature"] = 1
                            response = await self.client.chat.completions.create(**kwargs)
                        # If max_tokens also fails, try without limit
                        elif "max_tokens" in error_msg2 and "not supported" in error_msg2:
                            logger.warning("Neither max parameter supported, trying without token limit")
                            kwargs.pop("max_tokens", None)
                            try:
                                response = await self.client.chat.completions.create(**kwargs)
                            except Exception as e3:
                                # Check temperature again after removing max_tokens
                                if "temperature" in str(e3) and "not support" in str(e3):
                                    logger.warning("Using default temperature=1")
                                    kwargs["temperature"] = 1
                                    response = await self.client.chat.completions.create(**kwargs)
                                else:
                                    raise
                        else:
                            raise
                elif "max_tokens" in error_msg and "not supported" in error_msg and "max_completion_tokens" in error_msg:
                    # API says use max_completion_tokens instead of max_tokens
                    logger.debug("max_tokens not supported by API, already tried max_completion_tokens")
                    raise
                elif "temperature" in error_msg and ("not support" in error_msg or "only the default" in error_msg.lower()):
                    kwargs["temperature"] = 1
                    response = await self.client.chat.completions.create(**kwargs)
                else:
                    raise
            
            content = response.choices[0].message.content
            
            # Log usage concisely
            if hasattr(response, 'usage'):
                logger.debug(f"LLM Usage: {response.usage.total_tokens} tokens")
            
            if return_full_response:
                return response
                
            return content
        
        except Exception as e:
            error_msg = str(e)
            if "Connection error" in error_msg:
                detailed_msg = f"Failed to connect to Azure OpenAI at {settings.azure_openai_endpoint}. Please check if the endpoint URL and API key are correct in your .env file."
                logger.error(detailed_msg)
                raise HTTPException(
                    status_code=502,
                    detail=detailed_msg
                )
            logger.error(f"Error in chat completion: {error_msg}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        try:
            try:
                # Ensure input is a string and sanitize
                if isinstance(text, list):
                    text = text[0] if text else ""
                
                # Replace newlines which can negatively affect performance/validity of embeddings
                text = text.replace("\n", " ")
                
                response = await self.embedding_client.embeddings.create(
                    model=self.embedding_deployment,
                    input=[text] # Pass as list
                )
                return response.data[0].embedding
            except Exception as e:
                # If specific deployment fails, try fallback to standard ada-002
                if "DeploymentNotFound" in str(e) or "404" in str(e):
                    logger.warning(f"Primary embedding deployment '{self.embedding_deployment}' failed. Trying fallback 'text-embedding-ada-002'...")
                    response = await self.embedding_client.embeddings.create(
                        model="text-embedding-ada-002",
                        input=text
                    )
                    return response.data[0].embedding
                raise

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts in one API call.
        """
        try:
            # Sanitize texts: replace newlines
            sanitized_texts = [t.replace("\n", " ") for t in texts]
            
            response = await self.embedding_client.embeddings.create(
                model=self.embedding_deployment,
                input=sanitized_texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            # Fallback to individual if batch fails (e.g. context length exceeded)
            results = []
            for text in texts:
                emb = await self.generate_embedding(text)
                results.append(emb)
            return results

    async def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.5
    ) -> str:
        """
        Generate structured JSON output.
        
        Args:
            system_prompt: System instruction
            user_prompt: User query
            temperature: Sampling temperature
        
        Returns:
            JSON string response
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=2500, # Structure can be large
            response_format={"type": "json_object"}
        )
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Input text
        
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
    
    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Stream chat completion.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens
        
        Yields:
            Chunks of generated text
        """
        try:
            kwargs = {
                "model": self.deployment,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }
            
            # Try with max_completion_tokens first (GPT-5.x models)
            try:
                kwargs["max_completion_tokens"] = max_tokens
                stream = await self.client.chat.completions.create(**kwargs)
            except (TypeError, Exception) as e:
                error_msg = str(e)
                
                # Check if it's a parameter compatibility issue
                if "max_completion_tokens" in error_msg and ("not supported" in error_msg or "unexpected keyword" in error_msg):
                    # Library doesn't support max_completion_tokens, try max_tokens
                    logger.debug("max_completion_tokens not supported in streaming, trying max_tokens")
                    kwargs.pop("max_completion_tokens", None)
                    kwargs["max_tokens"] = max_tokens
                    try:
                        stream = await self.client.chat.completions.create(**kwargs)
                    except Exception as e2:
                        error_msg2 = str(e2)
                        # Check for temperature restrictions
                        if "temperature" in error_msg2 and ("not support" in error_msg2 or "only the default" in error_msg2.lower()):
                            logger.warning(f"Temperature {kwargs.get('temperature')} not supported in streaming, using temperature=1")
                            kwargs["temperature"] = 1
                            stream = await self.client.chat.completions.create(**kwargs)
                        # If max_tokens also fails, try without limit
                        elif "max_tokens" in error_msg2 and "not supported" in error_msg2:
                            logger.warning("Neither max parameter supported in streaming, trying without token limit")
                            kwargs.pop("max_tokens", None)
                            try:
                                stream = await self.client.chat.completions.create(**kwargs)
                            except Exception as e3:
                                if "temperature" in str(e3) and "not support" in str(e3):
                                    logger.warning("Using default temperature=1 in streaming")
                                    kwargs["temperature"] = 1
                                    stream = await self.client.chat.completions.create(**kwargs)
                                else:
                                    raise
                        else:
                            raise
                elif "max_tokens" in error_msg and "not supported" in error_msg and "max_completion_tokens" in error_msg:
                    # API says use max_completion_tokens instead
                    logger.debug("max_tokens not supported by API in streaming, already tried max_completion_tokens")
                    raise
                # Check for temperature restrictions
                elif "temperature" in error_msg and ("not support" in error_msg or "only the default" in error_msg.lower()):
                    logger.warning(f"Temperature {kwargs.get('temperature')} not supported in streaming, using temperature=1")
                    kwargs["temperature"] = 1
                    stream = await self.client.chat.completions.create(**kwargs)
                else:
                    # Different error, re-raise
                    raise
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"Error in streaming completion: {str(e)}")
            raise


# Global service instance
azure_openai_service = AzureOpenAIService()
