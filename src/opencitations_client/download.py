"""Download data in bulk."""

import contextlib
import csv
import io
import tarfile
import zipfile
from collections.abc import Generator, Iterable
from pathlib import Path
from typing import TextIO

import figshare_client
import pystow
import zenodo_client
from pystow.utils import open_inner_zipfile, open_zip_reader, safe_open_reader, safe_open_writer
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
]

METADATA_RECORD_ID = "15625650"
METADATA_LATEST_VERSION = "13"
METADATA_NAME = "output_csv_2026_01_14.tar.gz"
METADATA_LENGTH = 129_436_832

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
    with _iterate_metadata_files(path) as files:
        for _, file in files:
            reader = csv.DictReader(file, fieldnames=METADATA_COLUMNS)
            for record in tqdm(reader, total=METADATA_LENGTH, unit="document", unit_scale=True):
                yield _process_metadata(record)


def iter_omid_to_doi() -> Iterable[tuple[str, str]]:
    """Get OMID to DOI."""
    yield from _iter_omid_to_external_identifier("doi")


def iter_omid_to_pubmed() -> Iterable[tuple[str, str]]:
    """Get OMID to PubMed identifier."""
    yield from _iter_omid_to_external_identifier("pmid")


def _iter_omid_to_external_identifier(prefix: str) -> Iterable[tuple[str, str]]:
    if False:
        path = ensure_metadata_csv()
    else:
        path = Path.home().joinpath(
            ".data", "zenodo", METADATA_RECORD_ID, METADATA_LATEST_VERSION, METADATA_NAME
        )
    with _iterate_metadata_files(path) as files:
        for member, file in files:
            next(file)  # throw away header, which has a bunch of junk
            for line in file:
                curies, _, _ = line.partition(",")
                references = {}
                for curie in curies.split():
                    _prefix, _, identifier = curie.partition(":")
                    if not identifier:
                        continue
                    references[_prefix] = identifier
                try:
                    omid = references["omid"]
                except KeyError:
                    tqdm.write(f"[{member.name}] bad line: {line}")
                    continue
                if external_identifier := references.get(prefix):
                    yield omid, external_identifier


def _iterate_tar_info(tar: tarfile.TarFile) -> Iterable[tuple[tarfile.TarInfo, TextIO]]:
    for member in tqdm(tar.getmembers(), unit="file", unit_scale=True, desc="extracting metadata"):
        if not member.name.endswith(".csv"):
            continue
        f = tar.extractfile(member)
        if f is None:
            continue
        yield member, io.TextIOWrapper(f, encoding="utf-8")


@contextlib.contextmanager
def _iterate_metadata_files(
    path: Path,
) -> Generator[Iterable[tuple[tarfile.TarInfo, TextIO]], None, None]:
    with tarfile.open(path, "r") as tar:
        yield _iterate_tar_info(tar)


def get_omid_to_pubmed(force_process: bool = False) -> dict[str, str]:
    """Get a dictionary from OMIDs to PubMed identifiers."""
    path = pystow.join(
        "zenodo", METADATA_RECORD_ID, METADATA_LATEST_VERSION, name="omid_to_pubmed.tsv.gz"
    )
    if path.is_file() and not force_process:
        with safe_open_reader(path) as file:
            return dict(file)
    rv = {}
    with safe_open_writer(path) as writer:
        writer.writerow(("omid", "pubmed"))
        for omid, pmid in iter_omid_to_pubmed():
            writer.writerow((omid, pmid))
            rv[omid] = pmid
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
        with zipfile.ZipFile(path, mode="r") as zip_file:
            for info in zip_file.infolist():
                if not info.filename.endswith(".csv"):
                    continue
                with open_inner_zipfile(
                    zip_file, info.filename, operation="read", representation="text"
                ) as file:
                    for record in csv.DictReader(file):
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


# This is a file of citations that has OIDs but has been pre-subset
# for ones corresponding to Pubmed, but without actually giving the pmids
POCI = "https://figshare.com/ndownloader/files/53266736"


def ensure_poci() -> Path:
    """Enable the POCI data."""
    return pystow.ensure(
        "figshare",
        str(SOURCE_CSV_ID),
        url=POCI,
        name="poci-2023_08_14-23.zip",
    )


def get_pubmed_citations(force_process: bool = False) -> list[tuple[str, str]]:
    """Get pubmed citations."""
    out_path = MODULE.join(
        "zenodo",
        METADATA_RECORD_ID,
        METADATA_LATEST_VERSION,
        name="pubmed_citations.tsv.gz",
    )
    if out_path.is_file() and not force_process:
        with safe_open_reader(out_path) as file:
            return list(file)  # type:ignore[arg-type]

    rv = []
    omid_to_pubmed = get_omid_to_pubmed()
    with (
        open_zip_reader(ensure_poci(), inner_path="poci-2023_08_14-23.csv", delimiter=",") as reader,
        safe_open_writer(out_path) as writer,
    ):
        next(reader)
        for citation, _source in tqdm(reader):
            left, _, right = citation.partition("-")
            left_pmid = omid_to_pubmed.get(f"br/{left}")
            right_pmid = omid_to_pubmed.get(f"br/{right}")
            if left_pmid and right_pmid:
                writer.writerow((left_pmid, right_pmid))
                rv.append((left_pmid, right_pmid))
    return rv


def ensure_source_nt() -> list[Path]:
    """Ensure the source data in NT format (23 GB zipped, 104 GB uncompressed)."""
    record_id = 24427051  # see https://doi.org/10.6084/m9.figshare.24427051
    return list(figshare_client.ensure_files(record_id))
