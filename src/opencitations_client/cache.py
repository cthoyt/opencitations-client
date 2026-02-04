"""Database operations."""

from functools import lru_cache
from typing import Literal, overload

from curies import Reference
from pystow.graph import GraphCache, GraphCachePaths, build_graph_cache

from .download import MODULE, iter_doi_citations, iter_omid_citations, iter_pubmed_citations
from .models import Citation, CitationReturnType, handle_input

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
    if not doi_cache_paths.exists():
        return build_graph_cache(iter_doi_citations, doi_cache_paths, estimated_edges=1_191_000_000)
    return GraphCache(doi_cache_paths)


def _get_cache(prefix: str) -> GraphCache:
    match prefix:
        case "pmid" | "pubmed":
            return _get_pubmed_cache()
        case "omid":
            return _get_omid_cache()
        case "doi":
            return _get_doi_cache()
        case _:
            raise NotImplementedError(f"citation lookup not implemented for prefix: {prefix}")


# docstr-coverage:excused `overload`
@overload
def get_outgoing_citations(
    reference: str | Reference, *, return_type: Literal["citation"] = ...
) -> list[Citation]: ...


# docstr-coverage:excused `overload`
@overload
def get_outgoing_citations(
    reference: str | Reference, *, return_type: Literal["reference"] = ...
) -> list[Reference]: ...


# docstr-coverage:excused `overload`
@overload
def get_outgoing_citations(
    reference: str | Reference, *, return_type: Literal["str"] = ...
) -> list[str]: ...


def get_outgoing_citations(
    reference: str | Reference, *, return_type: CitationReturnType = "reference"
) -> list[Citation] | list[Reference] | list[str]:
    """Get outgoing citations as a list of local unique identifiers."""
    if return_type == "citation":
        raise NotImplementedError("cache-based citation lookup can't return full citation yet")
    reference = handle_input(reference)
    identifiers = _get_cache(reference.prefix).out_edges(reference.identifier)
    if return_type == "str":
        return identifiers
    return [Reference(prefix=reference.prefix, identifier=identifier) for identifier in identifiers]


# docstr-coverage:excused `overload`
@overload
def get_incoming_citations(
    reference: str | Reference, *, return_type: Literal["citation"] = ...
) -> list[Citation]: ...


# docstr-coverage:excused `overload`
@overload
def get_incoming_citations(
    reference: str | Reference, *, return_type: Literal["reference"] = ...
) -> list[Reference]: ...


# docstr-coverage:excused `overload`
@overload
def get_incoming_citations(
    reference: str | Reference, *, return_type: Literal["str"] = ...
) -> list[str]: ...


def get_incoming_citations(
    reference: str | Reference, *, return_type: CitationReturnType = "reference"
) -> list[Citation] | list[Reference] | list[str]:
    """Get incoming citations as a list of local unique identifiers."""
    if return_type == "citation":
        raise NotImplementedError("cache-based citation lookup can't return full citation yet")
    reference = handle_input(reference)
    identifiers = _get_cache(reference.prefix).in_edges(reference.identifier)
    if return_type == "str":
        return identifiers
    return [Reference(prefix=reference.prefix, identifier=identifier) for identifier in identifiers]
