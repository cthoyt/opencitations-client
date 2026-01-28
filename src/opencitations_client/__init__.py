"""Access and download data from OpenCitations."""

from .api import CitationsResponse, get_citations

__all__ = [
    "CitationsResponse",
    "get_citations",
]
