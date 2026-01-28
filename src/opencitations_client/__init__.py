"""Access and download data from OpenCitations."""

from .api import Citation, get_incoming_citations, get_outgoing_citations

__all__ = [
    "Citation",
    "get_incoming_citations",
    "get_outgoing_citations",
]
