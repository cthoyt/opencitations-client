"""Download data in bulk."""

import csv
import zipfile
from collections.abc import Iterable
from pathlib import Path

import figshare_client
import zenodo_client
from pystow.utils import open_inner_zipfile

from .api import Citation, _process

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
]


def ensure_metadata_csv() -> Path:
    """Ensure the metadata in CSV format (12 GB compressed, 49 GB uncompressed).

    .. seealso:: https://zenodo.org/records/15625651
    """
    return zenodo_client.download_zenodo("15625651", name="oc_meta_data_2025-06-06.tar.gz")


def ensure_metadata_kubernetes() -> list[Path]:
    """Ensure the metadata in Kubernetes format (39 GB compressed, 187 GB uncompressed).

    .. seealso:: https://doi.org/10.5281/zenodo.15855111
    """
    raise NotImplementedError(
        "waiting on https://github.com/cthoyt/zenodo-client/pull/53 to implement "
        '`return zenodo_client.ensure_files("15855111")`'
    )


def ensure_metadata_rdf() -> list[Path]:
    """Ensure metadata/provenance data in RDF format (46.5 GB compressed, 66 GB uncompressed).

    .. seealso:: https://doi.org/10.5281/zenodo.17483301
    """
    raise NotImplementedError(
        "waiting on https://github.com/cthoyt/zenodo-client/pull/53 to implement "
        '`zenodo_client.ensure_files("15855111")`'
    )


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


def ensure_source_csv() -> list[Path]:
    """Ensure the source data in CSV format (25.7 GB zipped, 426 GB uncompressed)."""
    record_id = 28677293  # see https://doi.org/10.6084/m9.figshare.28677293
    return list(figshare_client.ensure_files(record_id))


def ensure_source_nt() -> list[Path]:
    """Ensure the source data in NT format (23 GB zipped, 104 GB uncompressed)."""
    record_id = 24427051  # see https://doi.org/10.6084/m9.figshare.24427051
    return list(figshare_client.ensure_files(record_id))


# This is a file of citations that has OIDs but has been pre-subset
# for ones corresponding to Pubmed, but without actually giving the pmids
POCI = "https://figshare.com/ndownloader/files/53266736"

#
METADATA_URL = "https://zenodo.org/records/18324537/files/output_csv_2026_01_14.tar.gz?download=1"
