"""Download data in bulk."""

from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

import figshare_client
import pystow
import zenodo_client
from pystow.utils import (
    iter_tarred_csvs,
    iter_zipped_csvs,
    safe_open_reader,
    safe_open_writer,
)
from tqdm import tqdm

from .api import Citation, Metadata, _process, _process_metadata

__all__ = [
    "ensure_citation_data_csv",
    "ensure_citation_data_nt",
    "ensure_citation_data_scholix",
    "ensure_metadata_csv",
    "ensure_metadata_kubernetes",
    "ensure_metadata_rdf",
    "ensure_provenance_data_csv",
    "ensure_provenance_data_nt",
    "ensure_provenance_rdf",
    "ensure_source_csv",
    "ensure_source_nt",
    "get_pubmed_citations",
    "iter_doi_citations",
    "iter_omid_citations",
    "iter_pubmed_citations",
]

METADATA_RECORD_ID = "15625650"
METADATA_LATEST_VERSION = "13"
METADATA_NAME = "output_csv_2026_01_14.tar.gz"
METADATA_LENGTH = 129_436_832
CITATIONS_LENGTH = 2_693_728_426

MODULE = pystow.module("opencitations")


def ensure_metadata_csv() -> Path:
    """Ensure the metadata in CSV format (12 GB compressed, 49 GB uncompressed).

    .. seealso:: https://zenodo.org/records/15625650
    """
    return zenodo_client.download_zenodo(METADATA_RECORD_ID, name=METADATA_NAME)


METADATA_COLUMNS = [
    "id",
    "title",
    "author",
    "issue",
    "volume",
    "venue",
    "page",
    "pub_date",
    "type",
    "publisher",
    "editor",
]


def iter_metadata() -> Iterable[Metadata]:
    """Iterate over all documents."""
    path = ensure_metadata_csv()
    for record in iter_tarred_csvs(
        path, return_type="record", progress=True, max_line_length=100_000
    ):
        yield _process_metadata(record)


def get_doi_from_omid(omid: str) -> str | None:
    """Get a DOI for the given OMID."""
    return get_omid_to_doi().get(omid)


def get_omid_from_doi(doi: str) -> str | None:
    """Get an OMID for the given DOI."""
    return get_doi_to_omid().get(doi)


@lru_cache(1)
def get_doi_to_omid() -> dict[str, str]:
    """Get a mapping from DOI to OMID."""
    return {doi: omid for omid, doi in get_omid_to_doi().items()}


@lru_cache(1)
def get_omid_to_doi(*, force_process: bool = False) -> dict[str, str]:
    """Get OMID to DOI dictionary."""
    return _get_omid_to_external("pmid", force_process=force_process)


def iter_omid_to_doi() -> Iterable[tuple[str, str]]:
    """Get OMID to DOI."""
    yield from _iter_omid_to_external_identifier("doi")


def get_pubmed_from_omid(omid: str) -> str | None:
    """Get a PubMed ID for the given OMID."""
    return get_omid_to_pubmed().get(omid)


def get_omid_from_pubmed(pubmed: str | int) -> str | None:
    """Get and OMID for the given PubMed ID."""
    return get_pubmed_to_omid().get(str(pubmed))


@lru_cache(1)
def get_pubmed_to_omid() -> dict[str, str]:
    """Get a mapping from PubMed to OMID."""
    return {pubmed: omid for omid, pubmed in get_omid_to_pubmed().items()}


def iter_omid_to_pubmed() -> Iterable[tuple[str, str]]:
    """Get OMID to PubMed identifier."""
    yield from _iter_omid_to_external_identifier("pmid")


def _iter_omid_to_external_identifier(prefix: str) -> Iterable[tuple[str, str]]:
    path = ensure_metadata_csv()
    for curies, *_ in iter_tarred_csvs(path, max_line_length=100_000):
        references = {}
        for curie in curies.split():
            _prefix, _, identifier = curie.partition(":")
            if not identifier:
                continue
            references[_prefix] = identifier
        try:
            omid = references["omid"]
        except KeyError:
            tqdm.write(f"bad curies: {curies}")
            continue
        if external_identifier := references.get(prefix):
            yield omid, external_identifier


@lru_cache(1)
def get_omid_to_pubmed(*, force_process: bool = False) -> dict[str, str]:
    """Get a dictionary from OMIDs to PubMed identifiers."""
    return _get_omid_to_external("pmid", force_process=force_process)


def _get_omid_to_external(prefix: str, *, force_process: bool = False) -> dict[str, str]:
    """Get a dictionary from OMIDs to PubMed identifiers."""
    path = MODULE.join(name=f"omid_to_{prefix}.tsv.gz")
    if path.is_file() and not force_process:
        with safe_open_reader(path) as file:
            _header = next(file)
            return dict(file)
    rv = {}
    with safe_open_writer(path) as writer:
        writer.writerow(("omid", prefix))
        for omid_id, external_id in _iter_omid_to_external_identifier(prefix):
            writer.writerow((omid_id, external_id))
            rv[omid_id] = external_id
    return rv


def ensure_metadata_kubernetes() -> list[Path]:
    """Ensure the metadata in Kubernetes format (39 GB compressed, 187 GB uncompressed).

    .. seealso:: https://doi.org/10.5281/zenodo.15855111
    """
    return zenodo_client.download_all_zenodo("15855111")


def ensure_metadata_rdf() -> list[Path]:
    """Ensure metadata/provenance data in RDF format (46.5 GB compressed, 66 GB uncompressed).

    .. seealso:: https://doi.org/10.5281/zenodo.17483301
    """
    return zenodo_client.download_all_zenodo("17483301")


def ensure_provenance_rdf() -> list[Path]:
    """Ensure the provenance data in RDF format (154 GB compressed, 1 TB uncompressed)."""
    record_id = 29543783  # see https://doi.org/10.6084/m9.figshare.29543783
    return list(figshare_client.ensure_files(record_id))


def ensure_citation_data_csv() -> list[Path]:
    """Ensure the citation data in CSV format (38.8 GB zipped, 242 GB uncompressed)."""
    record_id = 24356626  # see https://doi.org/10.6084/m9.figshare.24356626
    return list(figshare_client.ensure_files(record_id))


def iterate_citations() -> Iterable[Citation]:
    """Download all files and iterate over all citations."""
    for path in ensure_citation_data_csv():
        for record in iter_zipped_csvs(path, return_type="record"):
            yield _process(record)


def ensure_citation_data_nt() -> list[Path]:
    """Ensure the citation data in n-triple format (87.4 GB zipped, 2.1 TB uncompressed)."""
    record_id = 24369136  # see https://doi.org/10.6084/m9.figshare.24369136
    return list(figshare_client.ensure_files(record_id))


def ensure_citation_data_scholix() -> list[Path]:
    """Ensure the citation data in Scholix format (45 GB zipped, 2.1 TB uncompressed)."""
    record_id = 24416749  # see https://doi.org/10.6084/m9.figshare.24416749
    return list(figshare_client.ensure_files(record_id))


def ensure_provenance_data_csv() -> list[Path]:
    """Ensure the provenance data in CSV format (20 GB zipped, 454 GB uncompressed)."""
    record_id = 24417733  # see https://doi.org/10.6084/m9.figshare.24417733
    return list(figshare_client.ensure_files(record_id))


def ensure_provenance_data_nt() -> list[Path]:
    """Ensure the provenance data in n-triples format (105 GB zipped, 3.4 TB uncompressed)."""
    record_id = 24417736  # see https://doi.org/10.6084/m9.figshare.24417736
    return list(figshare_client.ensure_files(record_id))


SOURCE_CSV_ID = 28677293  # see https://doi.org/10.6084/m9.figshare.28677293


def ensure_source_csv() -> list[Path]:
    """Ensure the source data in CSV format (25.7 GB zipped, 426 GB uncompressed)."""
    return list(figshare_client.ensure_files(SOURCE_CSV_ID))


def get_pubmed_citations(*, force_process: bool = False) -> list[tuple[str, str]]:
    """Get PubMed-PubMed citations."""
    return list(_get_external_citations("pmid", force_process=force_process))


def iter_pubmed_citations(*, force_process: bool = False) -> Iterable[tuple[str, str]]:
    """Get PubMed-PubMed citations."""
    return _get_external_citations("pmid", force_process=force_process)


def iter_doi_citations(*, force_process: bool = False) -> Iterable[tuple[str, str]]:
    """Get DOI-DOI citations."""
    return _get_external_citations("doi", force_process=force_process)


def _get_external_citations(
    prefix: str, *, force_process: bool = False
) -> Iterable[tuple[str, str]]:
    out_path = MODULE.join(name=f"{prefix}_citations.tsv.gz")
    if out_path.is_file() and not force_process:
        with safe_open_reader(out_path) as reader:
            yield from reader
    else:
        omid_to_external = _get_omid_to_external(prefix, force_process=force_process)
        with safe_open_writer(out_path) as writer:
            for path in tqdm(ensure_citation_data_csv(), desc="reading citations", unit="archive"):
                for citation, *_ in iter_zipped_csvs(path, progress=True):
                    left, _, right = citation.lstrip("oci:").partition("-")
                    source_external_id = omid_to_external.get(f"br/{left}")
                    target_external_id = omid_to_external.get(f"br/{right}")
                    if source_external_id and target_external_id:
                        writer.writerow((source_external_id, target_external_id))
                        yield source_external_id, target_external_id


def iter_omid_citations(*, force_process: bool = False) -> Iterable[tuple[str, str]]:
    """Iterate citations between OpenCitation identifiers."""
    out_path = MODULE.join(name="omid_citations.tsv.gz")
    if out_path.is_file() and not force_process:
        with safe_open_reader(out_path) as reader:
            yield from reader
    else:
        with safe_open_writer(out_path) as writer:
            for path in tqdm(ensure_citation_data_csv(), desc="reading citations", unit="archive"):
                for citation, *_ in iter_zipped_csvs(path, progress=True):
                    left, _, right = citation.lstrip("oci:").partition("-")
                    source_external_id = f"br/{left}"
                    target_external_id = f"br/{right}"
                    writer.writerow((source_external_id, target_external_id))
                    yield source_external_id, target_external_id


def ensure_source_nt() -> list[Path]:
    """Ensure the source data in NT format (23 GB zipped, 104 GB uncompressed)."""
    record_id = 24427051  # see https://doi.org/10.6084/m9.figshare.24427051
    return list(figshare_client.ensure_files(record_id))
