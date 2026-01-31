"""Database operations."""

from opencitations_client.download import iter_pubmed_citations, MODULE
from pystow.graph import build_graph_cache, GraphCache, GraphCachePaths
from functools import lru_cache

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
    build_graph_cache(iter_pubmed_citations, directory, estimated_edges=198_000_000)


@lru_cache(1)
def _get_cache() -> GraphCache:
    # takes about 9 seconds to warm up
    return GraphCache.from_directory(directory)


def get_outgoing_citations(pmid: str) -> list[str]:
    """Get outgoing citations as a list of PubMed identifiers."""
    if not paths.exists():
        raise FileNotFoundError
    return _get_cache().out_edges(pmid)


def get_incoming_citations(pmid: str) -> list[str]:
    """Get incoming citations as a list of PubMed identifiers."""
    if not paths.exists():
        raise FileNotFoundError
    return _get_cache().out_edges(pmid)


if __name__ == '__main__':
    import time

    s = time.time()
    _get_cache()
    print(f"warmed up cache in {time.time() - s:.2f} seconds")

    example = next(iter(_get_cache().forward.node_to_id))
    print(f'using example: pmid:{example}')

    s2 = time.time()
    print(get_outgoing_citations(example))
    print(f"got citation in {time.time() - s2:.2f} seconds")

    print("39514576")
    print(get_outgoing_citations("39514576"))
