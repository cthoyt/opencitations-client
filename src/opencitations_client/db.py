"""Database operations."""

from functools import lru_cache

from pystow.graph import GraphCache, GraphCachePaths, build_graph_cache

from .download import MODULE, iter_pubmed_citations

__all__ = [
    "get_incoming_citations",
    "get_outgoing_citations",
]

directory = MODULE.join("database-pmid")
paths = GraphCachePaths.from_directory(directory)


def build_pubmed_cache(*, force: bool = False) -> None:
    """Build a cache for PubMed-PubMed citations."""
    if paths.exists() and not force:
        return
    build_graph_cache(iter_pubmed_citations, directory, estimated_edges=191_000_000)


@lru_cache(1)
def _get_cache() -> GraphCache:
    # takes about 9 seconds to warm up
    return GraphCache.from_directory(directory)


def get_outgoing_citations(pubmed_id: str) -> list[str]:
    """Get outgoing citations as a list of PubMed identifiers."""
    if not paths.exists():
        raise FileNotFoundError
    return _get_cache().out_edges(pubmed_id)


def get_incoming_citations(pubmed_id: str) -> list[str]:
    """Get incoming citations as a list of PubMed identifiers."""
    if not paths.exists():
        raise FileNotFoundError
    return _get_cache().in_edges(pubmed_id)


if __name__ == "__main__":
    build_pubmed_cache()

    import time

    s = time.time()
    _get_cache()

    example = next(iter(_get_cache().forward.node_to_id))

    if example not in _get_cache().forward.node_to_id:
        raise KeyError(f"funny business for {example}")

    outgoing_citations = get_outgoing_citations(example)

    example_2 = next(iter(outgoing_citations))
    incoming_citations = get_incoming_citations(example_2)
    if example not in incoming_citations:
        pass

    # opencitations doesn't index this paper
