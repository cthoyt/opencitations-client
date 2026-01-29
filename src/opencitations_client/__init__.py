"""Access and download data from OpenCitations."""

from .api import (
    Citation,
    Metadata,
    Person,
    Publisher,
    Venue,
    get_articles,
    get_articles_for_author,
    get_articles_for_editor,
    get_incoming_citations,
    get_outgoing_citations,
)

__all__ = [
    "Citation",
    "Metadata",
    "Person",
    "Publisher",
    "Venue",
    "get_articles",
    "get_articles_for_author",
    "get_articles_for_editor",
    "get_incoming_citations",
    "get_outgoing_citations",
]
