"""
Base Agent Class using requests instead of OpenAI client
Author: Vinod Yadav
Date: 7-25-2025
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import requests
import json
import asyncio

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.api_key = self._get_api_key()
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
    def _get_api_key(self) -> str:
        """Get OpenAI API key"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return api_key
    
    async def invoke(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke the agent with a user message"""
        try:
            # Prepare the context information
            context_str = ""
            if context:
                context_str = f"\nContext: {context}"
            
            # Create the messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"{context_str}\n{user_message}"}
            ]
            
            # Get response from OpenAI
            response = await self._call_openai_api(messages)
            
            # Process the response
            result = await self.process_response(response, user_message, context)
            
            return {
                "agent_name": self.name,
                "message": result.get("message", response),
                "confidence": result.get("confidence", 0.8),
                "action_taken": result.get("action_taken"),
                "data": result.get("data", {})
            }
            
        except Exception as e:
            return {
                "agent_name": self.name,
                "message": f"Error processing request: {str(e)}",
                "confidence": 0.0,
                "action_taken": "error_handling",
                "data": {"error": str(e)}
            }
    
    async def _call_openai_api(self, messages: list) -> str:
        """Call OpenAI API using requests"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
                "messages": messages,
                "max_tokens": int(os.getenv("MAX_TOKENS", 1000)),
                "temperature": float(os.getenv("TEMPERATURE", 0.7))
            }
            
            # Run the synchronous request in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API returned status {response.status_code}: {response.text}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    @abstractmethod
    async def process_response(self, llm_response: str, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process the LLM response and return structured data"""
        pass
    
    def get_agent_info(self) -> Dict[str, str]:
        """Get basic information about the agent"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "description": self.system_prompt.split('\n')[0] if self.system_prompt else "No description"
        }