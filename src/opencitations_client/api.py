"""This is a placeholder for putting the main code for your module."""

import datetime
import re
from typing import Any, Literal

import pystow
import requests
from curies import Reference
from pydantic import BaseModel, Field, field_validator
from ratelimit import limits, sleep_and_retry

from opencitations_client.version import get_version

__all__ = [
    "Author",
    "Citation",
    "Metadata",
    "Publisher",
    "Venue",
    "get_author",
    "get_editor",
    "get_incoming_citations",
    "get_metadata",
    "get_outgoing_citations",
]

META_V1 = "https://api.opencitations.net/meta/v1"
BASE_V2 = "https://api.opencitations.net/index/v2"
AGENT = f"python-opencitations-client v{get_version()}"
CITATION_PREFIXES = {"doi", "pubmed", "omid"}


class Citation(BaseModel):
    """Wraps the results from a citation."""

    reference: Reference
    citing: list[Reference] = Field(
        ..., description="references to the article that cites the query article"
    )
    cited: list[Reference] = Field(..., description="references to the article that was queried")
    creation: datetime.date | None = None
    timespan: datetime.timedelta | None = None
    journal_self_citation: bool | None = None
    author_self_citation: bool | None = None

    @field_validator("creation", mode="before")
    @classmethod
    def parse_dates(cls, v: Any) -> Any:
        """Parse the creation field."""
        if isinstance(v, str):
            if len(v) == 4:  # YYYY
                return datetime.date.fromisoformat(v + "-01-01")
            if len(v) == 7:  # YYYY-MM
                return datetime.date.fromisoformat(v + "-01")
            if len(v) == 10:  # YYYY-MM-DD
                return datetime.date.fromisoformat(v)
        return v


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
    return [_process(record) for record in res.json()]


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
    return [_process(record) for record in res.json()]


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


def _process(record: dict[str, Any]) -> Citation:
    record["reference"] = Reference(prefix="oci", identifier=record.pop("oci"))
    record["journal_self_citation"] = _bool(record.pop("journal_sc"))
    record["author_self_citation"] = _bool(record.pop("author_sc"))
    record["citing"] = _process_curies(record.pop("citing"))
    record["cited"] = _process_curies(record.pop("cited"))
    return Citation.model_validate({k: v for k, v in record.items() if v})


def _process_curies(s: str) -> list[Reference]:
    return [Reference.from_curie(curie) for curie in s.split(" ")]


def _bool(s: Literal["yes", "no"]) -> bool:
    if s == "no":
        return False
    elif s == "yes":
        return True
    else:
        raise ValueError(f"invalid boolean value: {s}")


def _get_index_v2(part: str, *, token: str | None = None) -> requests.Response:
    return _get(f"{BASE_V2}/{part.lstrip('/')}", token=token)


METADATA_ID_RE = re.compile(
    r"(doi|issn|isbn|omid|openalex|pmid|pmcid):.+?(__(doi|issn|isbn|omid|openalex|pmid|pmcid):.+?)*$"
)


class Author(BaseModel):
    """Represents an author in OpenCitations."""

    name: str
    references: list[Reference]


class Venue(BaseModel):
    """Represents a venue in OpenCitations."""

    name: str
    references: list[Reference]


class Publisher(BaseModel):
    """Represents a publisher in OpenCitations."""

    name: str
    references: list[Reference]


class Metadata(BaseModel):
    """A representation of metadata."""

    references: list[Reference]
    title: str
    authors: list[Author]
    pub_date: datetime.date
    venue: Venue | None = None
    volume: str | None = None
    issue: str | None = None
    page: str | None = None
    publisher: Publisher | None = None
    type: str


def _process_metadata(record: dict[str, Any]) -> Metadata:
    raise NotImplementedError


def get_metadata(references: list[Reference]):
    """Get documents by reference."""
    "__".join(reference.curie for reference in references)


def get_author() -> list[Reference]:
    """Get documents incident to the author."""


def get_editor() -> list[Reference]:
    """Get documents incident to the editor."""


def _get_meta_v1(part: str, *, token: str | None = None) -> requests.Response:
    return _get(f"{META_V1}/{part.lstrip('/')}", token=token)


@sleep_and_retry
@limits(calls=180, period=60)  # the OpenCitations team told me 180 calls per minute
def _get(url: str, *, token: str | None = None) -> requests.Response:
    token = pystow.get_config("opencitations", "token", passthrough=token, raise_on_missing=True)
    return requests.get(url, headers={"authorization": token, "User-Agent": AGENT}, timeout=5)
