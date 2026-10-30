"""
Package LLM pour AutoClaim - Intégration OmniRoute (compatible OpenAI).
"""

from src.llm.client import LLMClient, EnrichedResult, get_llm_client

__all__ = ["LLMClient", "EnrichedResult", "get_llm_client"]
