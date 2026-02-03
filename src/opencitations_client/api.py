"""This is a placeholder for putting the main code for your module."""

from __future__ import annotations

import re

import pystow
import requests
from curies import Reference
from ratelimit import limits, sleep_and_retry

from .models import Citation, Work, process_citation, process_work
from .version import get_version

__all__ = [
    "get_articles",
    "get_articles_for_author",
    "get_articles_for_editor",
    "get_incoming_citations",
    "get_outgoing_citations",
]

META_V1 = "https://api.opencitations.net/meta/v1"
BASE_V2 = "https://api.opencitations.net/index/v2"
AGENT = f"python-opencitations-client v{get_version()}"
CITATION_PREFIXES = {"doi", "pubmed", "omid"}


def get_outgoing_citations(
    reference: str | Reference, *, token: str | None = None
) -> list[Citation]:
    """Get the articles that the given article cites, from OpenCitations.

    :param reference: The reference to get citations for
    :param token: The token to use for authentication.
        Loaded via :func:`pystow.get_config` if not given explicitly
    :return: A list of citations

    .. seealso::

        https://api.opencitations.net/index/v2#/references/{id}
    """
    res = _get_index_v2(f"/references/{_handle_input(reference)}", token=token)
    res.raise_for_status()
    return [process_citation(record) for record in res.json()]


def get_incoming_citations(
    reference: str | Reference, *, token: str | None = None
) -> list[Citation]:
    """Get the articles that cite a given article, from OpenCitations.

    :param reference: The reference to get citations for
    :param token: The token to use for authentication.
        Loaded via :func:`pystow.get_config` if not given explicitly
    :return: A list of citations

    .. seealso::

        https://api.opencitations.net/index/v2#/citations/{id}
    """
    res = _get_index_v2(f"/citations/{_handle_input(reference)}", token=token)
    res.raise_for_status()
    return [process_citation(record) for record in res.json()]


def _handle_input(reference: str | Reference) -> str:
    if isinstance(reference, str):
        reference = Reference.from_curie(reference)
    if reference.prefix not in CITATION_PREFIXES:
        raise ValueError(f"invalid prefix: {reference.prefix}, use one of {CITATION_PREFIXES}")
    if reference.prefix == "pubmed":
        # put it in the internal representation, which is non-standard
        return f"pmid:{reference.identifier}"
    else:
        return reference.curie


def _get_index_v2(part: str, *, token: str | None = None) -> requests.Response:
    return _get(f"{BASE_V2}/{part.lstrip('/')}", token=token)


METADATA_ID_RE = re.compile(
    r"(doi|issn|isbn|omid|openalex|pmid|pmcid):.+?(__(doi|issn|isbn|omid|openalex|pmid|pmcid):.+?)*$"
)

ALLOWED_ARTICLE_PREFIXES = {"doi", "issn", "isbn", "omid", "openalex", "pmid", "pmcid"}


def get_articles(references: list[Reference], *, token: str | None = None) -> list[Work]:
    """Get documents by reference.

    :param references: A list of references to articles, using
    :param token: The token to use for authentication.
        Loaded via :func:`pystow.get_config` if not given explicitly
    :return: A list of articles for the references

    .. seealso:: https://api.opencitations.net/meta/v1#/metadata/{ids}
    """
    invalid_references = [
        reference for reference in references if reference.prefix not in ALLOWED_ARTICLE_PREFIXES
    ]
    if invalid_references:
        raise ValueError(f"invalid references: {invalid_references}")

    value = "__".join(reference.curie for reference in references)
    res = _get_meta_v1(f"/metadata/{value}", token=token)
    res.raise_for_status()
    return [process_work(record) for record in res.json()]


def get_articles_for_author(reference: Reference, *, token: str | None = None) -> list[Work]:
    """Get documents incident to the author.

    :param reference: A reference for an author, using ``orcid`` or ``omid`` as a prefix
    :param token: The token to use for authentication.
        Loaded via :func:`pystow.get_config` if not given explicitly
    :return: A list of articles associated with the author

    .. seealso:: https://api.opencitations.net/meta/v1#/author/{id}
    """
    _raise_for_invalid_person(reference)
    res = _get_meta_v1(f"/author/{reference.curie}", token=token)
    res.raise_for_status()
    return [process_work(record) for record in res.json()]


def get_articles_for_editor(reference: Reference, *, token: str | None = None) -> list[Work]:
    """Get documents incident to the editor.

    :param reference: A reference for an editor, using ``orcid`` or ``omid`` as a prefix
    :param token: The token to use for authentication.
        Loaded via :func:`pystow.get_config` if not given explicitly
    :return: A list of articles associated with the editor

    .. seealso:: https://api.opencitations.net/meta/v1#/editor/{id}
    """
    _raise_for_invalid_person(reference)
    res = _get_meta_v1(f"/editor/{reference.curie}", token=token)
    res.raise_for_status()
    return [process_work(record) for record in res.json()]


def _raise_for_invalid_person(reference: Reference) -> None:
    if reference.prefix == "omid":
        if not reference.identifier.startswith("ra/"):
            raise ValueError
    elif reference.prefix == "orcid":
        pass
    else:
        raise ValueError


def _get_meta_v1(part: str, *, token: str | None = None) -> requests.Response:
    return _get(f"{META_V1}/{part.lstrip('/')}", token=token)


@sleep_and_retry
@limits(calls=180, period=60)  # the OpenCitations team told me 180 calls per minute
def _get(url: str, *, token: str | None = None) -> requests.Response:
    token = pystow.get_config("opencitations", "token", passthrough=token, raise_on_missing=True)
    return requests.get(url, headers={"authorization": token, "User-Agent": AGENT}, timeout=15)
