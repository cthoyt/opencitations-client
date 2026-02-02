"""This is a placeholder for putting the main code for your module."""

from __future__ import annotations

import datetime
import re
from typing import Any, Literal, TypeVar

import curies
import curies.utils
import pystow
import requests
from curies import Reference
from pydantic import BaseModel, Field, field_validator
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm

from opencitations_client.version import get_version

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

META_V1 = "https://api.opencitations.net/meta/v1"
BASE_V2 = "https://api.opencitations.net/index/v2"
AGENT = f"python-opencitations-client v{get_version()}"
CITATION_PREFIXES = {"doi", "pubmed", "omid"}

X = TypeVar("X", bound=BaseModel)


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


def _process_metadata(record: dict[str, Any]) -> Metadata:
    record["references"] = _process_curies(record.pop("id"))
    record["authors"] = _process_tagged_list(record.pop("author"), Person)
    if venue_raw := record.pop("venue"):
        try:
            record["venue"] = _process_tagged(venue_raw, Venue)
        except curies.utils.NoCURIEDelimiterError:
            tqdm.write(f"bad venue: {venue_raw}")
    if publisher_raw := record.pop("publisher"):
        try:
            record["publisher"] = _process_tagged_list(publisher_raw, Publisher)
        except curies.utils.NoCURIEDelimiterError:
            tqdm.write(f"bad publisher: {publisher_raw}")
    if editor_raw := record.pop("editor"):
        try:
            record["editors"] = _process_tagged_list(editor_raw, Person)
        except curies.utils.NoCURIEDelimiterError:
            tqdm.write(f"bad editor: {editor_raw}")
    return Metadata.model_validate(record)


def _process_tagged_list(s: str, cls: type[X]) -> list[X]:
    if not s:
        return []
    return [_process_tagged(x, cls) for x in s.split(";") if x.strip()]


def _process_tagged(part: str, cls: type[X]) -> X:
    part = part.strip()
    if not part.endswith("]"):
        raise ValueError(f"no brackets were given: {part}")
    # partition on the _last_ one because some names have brackets
    # in them
    name, _, rest = part.rpartition("[")
    references = _process_curies(rest.rstrip("]"))
    return cls(name=name.strip(), references=references)


def _bool(s: Literal["yes", "no"]) -> bool:
    if s == "no":
        return False
    elif s == "yes":
        return True
    else:
        raise ValueError(f"invalid boolean value: {s}")


def _get_index_v2(part: str, *, token: str | None = None) -> requests.Response:
    return _get(f"{BASE_V2}/{part.lstrip('/')}", token=token)


class Person(BaseModel):
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
    authors: list[Person]
    pub_date: datetime.date | None = None
    venue: Venue | None = None
    volume: str | None = None
    issue: str | None = None
    page: str | None = None
    publisher: list[Publisher] | None = None
    editors: list[Person] | None = None
    type: str

    @field_validator("pub_date", mode="before")
    @classmethod
    def parse_dates(cls, v: Any) -> Any:
        """Parse the creation field."""
        if not v:
            return None
        if isinstance(v, str):
            if len(v) == 4:  # YYYY
                return datetime.date.fromisoformat(v + "-01-01")
            if len(v) == 7:  # YYYY-MM
                return datetime.date.fromisoformat(v + "-01")
            if len(v) == 10:  # YYYY-MM-DD
                return datetime.date.fromisoformat(v)
        return v

    @property
    def omid(self) -> str:
        """Get the OMID for the document."""
        for r in self.references:
            if r.prefix == "omid":
                return r.identifier
        raise ValueError(f"invalid omid: {self.omid}")

    @property
    def pubmed(self) -> str | None:
        """Get the PubMed identifier for the document, if it exists."""
        for r in self.references:
            if r.prefix == "pmid":
                return r.identifier
        return None


METADATA_ID_RE = re.compile(
    r"(doi|issn|isbn|omid|openalex|pmid|pmcid):.+?(__(doi|issn|isbn|omid|openalex|pmid|pmcid):.+?)*$"
)

ALLOWED_ARTICLE_PREFIXES = {"doi", "issn", "isbn", "omid", "pmid", "pmcid"}


def get_articles(references: list[Reference], *, token: str | None = None) -> list[Metadata]:
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
    return [_process_metadata(record) for record in res.json()]


def get_articles_for_author(reference: Reference, *, token: str | None = None) -> list[Metadata]:
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
    return [_process_metadata(record) for record in res.json()]


def get_articles_for_editor(reference: Reference, *, token: str | None = None) -> list[Metadata]:
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
    return [_process_metadata(record) for record in res.json()]


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
