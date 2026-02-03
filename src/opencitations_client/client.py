"""Access to OpenCitations."""

from functools import lru_cache

from .download import _get_omid_to_external

__all__ = [
    "get_doi_from_omid",
    "get_doi_to_omid",
    "get_omid_from_doi",
    "get_omid_from_pubmed",
    "get_omid_to_doi",
    "get_omid_to_pubmed",
    "get_pubmed_from_omid",
    "get_pubmed_to_omid",
]


def get_doi_from_omid(omid: str) -> str | None:
    """Get a DOI for the given OMID."""
    return get_omid_to_doi().get(omid)


def get_omid_from_doi(doi: str) -> str | None:
    """Get an OMID for the given DOI."""
    return get_doi_to_omid().get(doi)


@lru_cache(1)
def get_doi_to_omid(*, force_process: bool = False) -> dict[str, str]:
    """Get a mapping from DOIs to OMIDs."""
    return {doi: omid for omid, doi in get_omid_to_doi(force_process=force_process).items()}


@lru_cache(1)
def get_omid_to_doi(*, force_process: bool = False) -> dict[str, str]:
    """Get OMID to DOI dictionary."""
    return _get_omid_to_external("pmid", force_process=force_process)


def get_pubmed_from_omid(omid: str) -> str | None:
    """Get a PubMed ID for the given OMID."""
    return get_omid_to_pubmed().get(omid)


def get_omid_from_pubmed(pubmed: str | int) -> str | None:
    """Get an OMID for the given PubMed ID."""
    return get_pubmed_to_omid().get(str(pubmed))


@lru_cache(1)
def get_pubmed_to_omid(*, force_process: bool = False) -> dict[str, str]:
    """Get a mapping from PubMed identifiers to OMIDs."""
    return {
        pubmed: omid for omid, pubmed in get_omid_to_pubmed(force_process=force_process).items()
    }


@lru_cache(1)
def get_omid_to_pubmed(*, force_process: bool = False) -> dict[str, str]:
    """Get a mapping from OMIDs to PubMed identifiers."""
    return _get_omid_to_external("pmid", force_process=force_process)
