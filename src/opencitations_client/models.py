"""Object models for components of OpenCitations."""

from __future__ import annotations

import datetime
from collections.abc import Iterable
from typing import Any, Literal, TypeAlias, TypeVar

from curies import Reference
from curies.utils import NoCURIEDelimiterError
from pydantic import BaseModel, Field, field_validator
from tqdm import tqdm

__all__ = [
    "Citation",
    "CitationReturnType",
    "Person",
    "Publisher",
    "Venue",
    "Work",
    "process_citation",
    "process_work",
]

from opencitations_client.json_api_client import CITATION_PREFIXES


class Citation(BaseModel):
    """Wraps the results from a citation."""

    reference: Reference
    citing: list[Reference] = Field(...)
    cited: list[Reference] = Field(...)
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


class Work(BaseModel):
    """A representation of metadata for a creative work."""

    references: list[Reference]
    title: str
    authors: list[Person]
    pub_date: datetime.date | None = None
    venue: Venue | None = None
    volume: str | None = None
    issue: str | None = None
    page: str | None = None
    publishers: list[Publisher] | None = None
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
        if rv := get_reference_with_prefix(self.references, "omid"):
            return rv.identifier
        raise ValueError(f"invalid omid: {self.omid}")

    @property
    def pubmed(self) -> str | None:
        """Get the PubMed identifier for the document, if it exists."""
        if rv := get_reference_with_prefix(self.references, "pmid"):
            return rv.identifier
        return None


X = TypeVar("X", bound=BaseModel)


def process_citation(record: dict[str, Any]) -> Citation:
    """Process a citation record."""
    record["reference"] = Reference(prefix="oci", identifier=record.pop("oci"))
    record["journal_self_citation"] = _bool(record.pop("journal_sc"))
    record["author_self_citation"] = _bool(record.pop("author_sc"))
    record["citing"] = _process_curies(record.pop("citing"))
    record["cited"] = _process_curies(record.pop("cited"))
    return Citation.model_validate({k: v for k, v in record.items() if v})


def _process_curies(s: str) -> list[Reference]:
    return [Reference.from_curie(curie) for curie in s.split(" ")]


def process_work(record: dict[str, Any]) -> Work:
    """Process a metadata record for a creative work."""
    record["references"] = _process_curies(record.pop("id"))
    record["authors"] = _process_tagged_list(record.pop("author"), Person)
    if venue_raw := record.pop("venue"):
        try:
            record["venue"] = _process_tagged(venue_raw, Venue)
        except NoCURIEDelimiterError:
            tqdm.write(f"bad venue: {venue_raw}")
    if publisher_raw := record.pop("publisher"):
        try:
            record["publishers"] = _process_tagged_list(publisher_raw, Publisher)
        except NoCURIEDelimiterError:
            tqdm.write(f"bad publisher: {publisher_raw}")
    if editor_raw := record.pop("editor"):
        try:
            record["editors"] = _process_tagged_list(editor_raw, Person)
        except NoCURIEDelimiterError:
            tqdm.write(f"bad editor: {editor_raw}")
    return Work.model_validate(record)


def _process_tagged_list(s: str, cls: type[X]) -> list[X]:
    if not s:
        return []
    return [_process_tagged(x, cls) for x in s.split(";") if x.strip()]


def _process_tagged(part: str, cls: type[X]) -> X:
    part = part.strip()
    if not part.endswith("]"):
        raise ValueError(f"no brackets were given: {part}")
    # partition on the _last_ one because some names have brackets in them
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


def get_reference_with_prefix(references: Iterable[Reference], prefix: str) -> Reference | None:
    """Get a reference with the given prefix."""
    for reference in references:
        if reference.prefix == prefix:
            return reference
    return None


#: Citation return type
CitationReturnType: TypeAlias = Literal["citation", "reference", "str"]


def handle_input(reference: str | Reference) -> Reference:
    """Clean up a reference."""
    if isinstance(reference, str):
        reference = Reference.from_curie(reference)
    if reference.prefix not in CITATION_PREFIXES:
        raise ValueError(f"invalid prefix: {reference.prefix}, use one of {CITATION_PREFIXES}")
    if reference.prefix == "pubmed":
        # put it in the internal representation, which is non-standard
        return Reference(prefix="pmid", identifier=reference.identifier)
    return reference
