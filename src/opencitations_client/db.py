"""Database operations."""

from functools import lru_cache

from curies import Reference
from pystow.graph import GraphCache, GraphCachePaths, build_graph_cache

from .download import MODULE, iter_omid_citations, iter_pubmed_citations

__all__ = [
    "get_incoming_citations",
    "get_outgoing_citations",
]

pubmed_cache_paths = GraphCachePaths.from_directory(MODULE.join("database-pmid"))
omid_cache_paths = GraphCachePaths.from_directory(MODULE.join("database-omid"))
doi_cache_paths = GraphCachePaths.from_directory(MODULE.join("database-doi"))

CITATION_DB = MODULE.join(name="metadata.db")


@lru_cache(1)
def _get_pubmed_cache() -> GraphCache:
    if not pubmed_cache_paths.exists():
        return build_graph_cache(
            iter_pubmed_citations, pubmed_cache_paths, estimated_edges=191_000_000
        )
    # takes about 9 seconds to warm up
    return GraphCache(pubmed_cache_paths)


@lru_cache(1)
def _get_omid_cache() -> GraphCache:
    if not omid_cache_paths.exists():
        return build_graph_cache(
            iter_omid_citations, omid_cache_paths, estimated_edges=1_191_000_000
        )
    return GraphCache(omid_cache_paths)


@lru_cache(1)
def _get_doi_cache() -> GraphCache:
    if not omid_cache_paths.exists():
        return build_graph_cache(
            iter_omid_citations, doi_cache_paths, estimated_edges=1_191_000_000
        )
    return GraphCache(doi_cache_paths)


def get_outgoing_citations(reference: Reference) -> list[str]:
    """Get outgoing citations as a list of PubMed identifiers."""
    match reference.prefix:
        case "pmid" | "pubmed":
            return _get_pubmed_cache().out_edges(reference.identifier)
        case "omid":
            return _get_omid_cache().out_edges(reference.identifier)
        case "doi":
            return _get_omid_cache().out_edges(reference.identifier)
        case _:
            raise NotImplementedError(
                f"outgoing citation lookup not implemented for prefix: {reference.prefix}"
            )


def get_incoming_citations(reference: Reference) -> list[str]:
    """Get incoming citations as a list of PubMed identifiers."""
    match reference.prefix:
        case "pmid" | "pubmed":
            return _get_pubmed_cache().in_edges(reference.identifier)
        case "omid":
            return _get_omid_cache().in_edges(reference.identifier)
        case "doi":
            return _get_omid_cache().in_edges(reference.identifier)
        case _:
            raise NotImplementedError(
                f"incoming citation lookup not implemented for prefix: {reference.prefix}"
            )
