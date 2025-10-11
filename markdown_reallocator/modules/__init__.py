"""Application modules for document processing."""

from markdown_reallocator.modules.dedup import (
    DeduplicationModule,
    DeduplicationReport,
    SelectionStrategy,
)
from markdown_reallocator.modules.reorder import ReorderModule, ReorderStrategy
from markdown_reallocator.modules.search import SearchModule

__all__ = [
    "DeduplicationModule",
    "DeduplicationReport",
    "ReorderModule",
    "ReorderStrategy",
    "SearchModule",
    "SelectionStrategy",
]
