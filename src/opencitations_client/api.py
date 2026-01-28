"""This is a placeholder for putting the main code for your module."""

import datetime
from typing import Any, Literal

import pystow
import requests
from curies import Reference
from pydantic import BaseModel, field_validator

from opencitations_client.version import get_version

__all__ = [
    "CitationsResponse",
    "get_citations",
]

BASE_V2 = "https://api.opencitations.net/index/v2"
AGENT = f"python-opencitations-client v{get_version()}"
CITATION_PREFIXES = {"doi", "pubmed", "omid"}


class CitationsResponse(BaseModel):
    """Wraps the results from a citation."""

    reference: Reference
    citing: list[Reference]
    cited: list[Reference]
    creation: datetime.date
    timespan: str  # TODO this is the XSD duration format PnYnMnD;
    journal_self_citation: bool
    author_self_citation: bool

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


def get_citations(
    reference: str | Reference, *, token: str | None = None
) -> list[CitationsResponse]:
    """Get citations for a reference from OpenCitations.

    :param reference: The reference to get citations for
    :param token: The token to use for authentication.
        Loaded via :func:`pystow.get_config` if not given explicitly
    :return: A list of citations

    .. seealso::

        https://api.opencitations.net/index/v2#/citations/{id}
    """
    # see
    if isinstance(reference, str):
        reference = Reference.from_curie(reference)
    if reference.prefix not in CITATION_PREFIXES:
        raise ValueError(f"invalid prefix: {reference.prefix}, use one of {CITATION_PREFIXES}")

    res = _get_index_v2(f"/citations/{reference.curie}", token=token)
    res.raise_for_status()
    return [_process(record) for record in res.json()]


def _process(record: dict[str, Any]) -> CitationsResponse:
    record["reference"] = Reference(prefix="oci", identifier=record.pop("oci"))
    record["journal_self_citation"] = _bool(record.pop("journal_sc"))
    record["author_self_citation"] = _bool(record.pop("author_sc"))
    record["citing"] = [Reference.from_curie(curie) for curie in record.pop("citing").split(" ")]
    record["cited"] = [Reference.from_curie(curie) for curie in record.pop("cited").split(" ")]
    return CitationsResponse.model_validate(record)


def _bool(s: Literal["yes", "no"]) -> bool:
    if s == "no":
        return False
    elif s == "yes":
        return True
    else:
        raise ValueError(f"invalid boolean value: {s}")


def _get_index_v2(part: str, *, token: str | None = None) -> requests.Response:
    return _get(f"{BASE_V2}/{part.lstrip('/')}", token=token)


def _get(url: str, *, token: str | None = None) -> requests.Response:
    token = pystow.get_config("opencitations", "token", passthrough=token, raise_on_missing=True)
    return requests.get(url, headers={"authorization": token, "User-Agent": AGENT}, timeout=5)


if __name__ == "__main__":
    for _citation in get_citations("doi:10.1038/s41597-022-01807-3"):
        pass
