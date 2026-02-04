"""An abstraction over different ways of accessing OpenCitations."""

from typing import Literal, TypeAlias, overload

from curies import Reference

from .cache import get_incoming_citations_from_cache, get_outgoing_citations_from_cache
from .json_api_client import get_incoming_citations_from_api, get_outgoing_citations_from_api
from .models import Citation, CitationReturnType

__all__ = [
    "Backend",
    "get_incoming_citations",
    "get_outgoing_citations",
]

Backend: TypeAlias = Literal["api", "local"]


# docstr-coverage:excused `overload`
@overload
def get_outgoing_citations(
    reference: str | Reference,
    *,
    backend: Backend = ...,
    token: str | None = ...,
    return_type: Literal["str"] = ...,
) -> list[str]: ...


# docstr-coverage:excused `overload`
@overload
def get_outgoing_citations(
    reference: str | Reference,
    *,
    backend: Backend = ...,
    token: str | None = ...,
    return_type: Literal["reference"] = ...,
) -> list[Reference]: ...


# docstr-coverage:excused `overload`
@overload
def get_outgoing_citations(
    reference: str | Reference,
    *,
    backend: Backend = ...,
    token: str | None = ...,
    return_type: Literal["citation"] = ...,
) -> list[Citation]: ...


def get_outgoing_citations(
    reference: str | Reference,
    *,
    backend: Backend = "api",
    token: str | None = None,
    return_type: CitationReturnType = "reference",
) -> list[Citation] | list[Reference] | list[str]:
    """Get the articles that the given article cites, from OpenCitations.

    :param reference: The reference to get citations for
    :param backend: The backend to use (either web-based API or local cache)
    :param token: The token to use for authentication.
        Loaded via :func:`pystow.get_config` if not given explicitly
    :param return_type: The return type for citations. If using references or strings,
        will filter by the same prefix as the query reference
    :return: A list of citations

    .. seealso::

        https://api.opencitations.net/index/v2#/references/{id}
    """
    if backend == "api":
        return get_outgoing_citations_from_api(reference, token=token, return_type=return_type)
    elif backend == "local":
        return get_outgoing_citations_from_cache(reference, return_type=return_type)
    else:
        raise ValueError(f"backend {backend} not supported")


# docstr-coverage:excused `overload`
@overload
def get_incoming_citations(
    reference: str | Reference,
    *,
    backend: Backend = ...,
    token: str | None = ...,
    return_type: Literal["str"] = ...,
) -> list[str]: ...


# docstr-coverage:excused `overload`
@overload
def get_incoming_citations(
    reference: str | Reference,
    *,
    backend: Backend = ...,
    token: str | None = ...,
    return_type: Literal["reference"] = ...,
) -> list[Reference]: ...


# docstr-coverage:excused `overload`
@overload
def get_incoming_citations(
    reference: str | Reference,
    *,
    backend: Backend = ...,
    token: str | None = ...,
    return_type: Literal["citation"] = ...,
) -> list[Citation]: ...


def get_incoming_citations(
    reference: str | Reference,
    *,
    backend: Backend = "api",
    token: str | None = None,
    return_type: CitationReturnType = "reference",
) -> list[Citation] | list[Reference] | list[str]:
    """Get the articles that cite a given article, from OpenCitations.

    :param reference: The reference to get citations for
    :param backend: The backend to use (either web-based API or local cache)
    :param token: The token to use for authentication.
        Loaded via :func:`pystow.get_config` if not given explicitly
    :param return_type: The return type for citations. If using references or strings,
        will filter by the same prefix as the query reference
    :return: A list of citations

    .. seealso::

        https://api.opencitations.net/index/v2#/citations/{id}
    """
    if backend == "api":
        return get_incoming_citations_from_api(reference, token=token, return_type=return_type)
    elif backend == "local":
        return get_incoming_citations_from_cache(reference, return_type=return_type)
    else:
        raise ValueError(f"backend {backend} not supported")
