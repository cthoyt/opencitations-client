"""Access and download data from OpenCitations."""

from .api import Citation, get_incoming_citations, get_outgoing_citations
from .download import (
    ensure_citation_data_csv,
    ensure_citation_data_nt,
    ensure_citation_data_scholix,
    ensure_metadata_csv,
    ensure_metadata_kubernetes,
    ensure_metadata_rdf,
    ensure_provenance_data_csv,
    ensure_provenance_data_nt,
    ensure_provenance_rdf,
    ensure_source_csv,
    ensure_source_nt,
)

__all__ = [
    "Citation",
    "ensure_citation_data_csv",
    "ensure_citation_data_nt",
    "ensure_citation_data_scholix",
    "ensure_metadata_csv",
    "ensure_metadata_kubernetes",
    "ensure_metadata_rdf",
    "ensure_provenance_data_csv",
    "ensure_provenance_data_nt",
    "ensure_provenance_rdf",
    "ensure_source_csv",
    "ensure_source_nt",
    "get_incoming_citations",
    "get_outgoing_citations",
]
