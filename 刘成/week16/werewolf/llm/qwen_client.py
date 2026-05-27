"""Qwen API client for LLM calls."""

import os
import logging
import requests
from typing import Optional

from werewolf.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DEFAULT_MODEL

logger = logging.getLogger(__name__)


class QwenClient:
    """Client for Qwen API (compatible with OpenAI-style endpoint)."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """Initialize Qwen client."""
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.model = model
        self.base_url = DASHSCOPE_BASE_URL

        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY not set, LLM calls will use mock mode")

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """Send a chat request to Qwen API."""
        if not self.api_key:
            logger.warning("Using mock response (no API key)")
            return self._mock_response(user_prompt)

        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens,
            }

            logger.info(f"Calling LLM API with model: {self.model}")
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.info(f"LLM API response received: {content[:100]}...")
            return content

        except requests.exceptions.HTTPError as e:
            logger.error(f"LLM API HTTP error: {e}")
            if e.response and e.response.status_code == 404:
                logger.error(f"Model {self.model} not found, trying qwen-plus")
                # Fallback to qwen-plus
                data["model"] = "qwen-plus"
                try:
                    response = requests.post(url, headers=headers, json=data, timeout=60)
                    response.raise_for_status()
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
            return self._mock_response(user_prompt)
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return self._mock_response(user_prompt)

    def chat_with_history(self, system_prompt: str, history: list[dict], max_tokens: int = 2000) -> str:
        """Send a chat request with conversation history."""
        if not self.api_key:
            logger.warning("Using mock response (no API key)")
            return self._mock_response(str(history[-1] if history else ""))

        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            messages = [{"role": "system", "content": system_prompt}]
            for h in history:
                messages.append({
                    "role": h.get("role", "user"),
                    "content": h.get("content", "")
                })

            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return self._mock_response(str(history[-1] if history else ""))

    def _mock_response(self, prompt: str) -> str:
        """Generate a mock response when API is not available."""
        return f"Mock response to: {prompt[:100]}..."


# Global client instance
_client: Optional[QwenClient] = None


def get_client() -> QwenClient:
    """Get or create global LLM client."""
    global _client
    if _client is None:
        _client = QwenClient()
    return _client


def reset_client():
    """Reset global client (for testing)."""
    global _client
    _client = None