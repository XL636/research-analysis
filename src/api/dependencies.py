"""Shared FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache

from src.store.knowledge_base import KnowledgeBase


@lru_cache
def get_knowledge_base() -> KnowledgeBase:
    """Get shared KnowledgeBase instance."""
    return KnowledgeBase()
