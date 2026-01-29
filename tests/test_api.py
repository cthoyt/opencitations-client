"""API tests."""

import datetime
import unittest

from curies import Reference

from opencitations_client.api import (
    Author,
    Metadata,
    Publisher,
    Venue,
    _process_metadata,
    get_incoming_citations,
)
from opencitations_client.version import get_version


class TestVersion(unittest.TestCase):
    """Trivially test a version."""

    def test_version_type(self) -> None:
        """Test the version is a string.

        This is only meant to be an example test.
        """
        version = get_version()
        self.assertIsInstance(version, str)

    def test_get_citations(self) -> None:
        """Test getting citations."""
        bioregistry_reference = "doi:10.1038/s41597-022-01807-3"
        # this one cites the bioregistry paper
        psimi_reference = Reference.from_curie("doi:10.1021/acs.analchem.4c04091")

        citations = get_incoming_citations(bioregistry_reference)
        self.assertTrue(
            any(
                reference == psimi_reference
                for citation in citations
                for reference in citation.citing
            )
        )

    def test_process_metadata(self) -> None:
        """Test parsing a metadata record returned from the API."""
        data = {
            "id": "doi:10.1007/s11192-022-04367-w openalex:W3214893238 omid:br/061202127149",
            "title": "Identifying And Correcting Invalid Citations Due To "
            "DOI Errors In Crossref Data",
            "author": "Cioffi, Alessia [orcid:0000-0002-9812-4065 omid:ra/061206532419]; "
            "Coppini, Sara [orcid:0000-0002-6279-3830 omid:ra/061206532420]; "
            "Massari, Arcangelo [orcid:0000-0002-8420-0696 omid:ra/06250110138]; "
            "Moretti, Arianna [orcid:0000-0001-5486-7070 omid:ra/061206532421]; "
            "Peroni, Silvio [orcid:0000-0003-0530-4305 omid:ra/0614010840729]; "
            "Santini, Cristian [orcid:0000-0001-7363-6737 omid:ra/067099715]; "
            "Shahidzadeh, Nooshin [orcid:0000-0003-4114-074X omid:ra/06220110984]",
            "pub_date": "2022-06",
            "issue": "6",
            "volume": "127",
            "venue": "Scientometrics "
            "[issn:0138-9130 issn:1588-2861 openalex:S148561398 omid:br/0626055628]",
            "type": "journal article",
            "page": "3593-3612",
            "publisher": "Springer Science And Business Media Llc "
            "[crossref:297 omid:ra/0610116006]",
            "editor": "",
        }
        expected = Metadata(
            references=[
                Reference.from_curie("doi:10.1007/s11192-022-04367-w"),
                Reference.from_curie("openalex:W3214893238"),
                Reference.from_curie("omid:br/061202127149"),
            ],
            title="Identifying And Correcting Invalid Citations Due To DOI Errors In Crossref Data",
            authors=[
                Author(
                    name="Cioffi, Alessia",
                    references=[
                        Reference.from_curie("orcid:0000-0002-9812-4065"),
                        Reference.from_curie("omid:ra/061206532419"),
                    ],
                ),
                Author(
                    name="Coppini, Sara",
                    references=[
                        Reference.from_curie("orcid:0000-0002-6279-3830"),
                        Reference.from_curie("omid:ra/061206532420"),
                    ],
                ),
                Author(
                    name="Massari, Arcangelo",
                    references=[
                        Reference.from_curie("orcid:0000-0002-8420-0696"),
                        Reference.from_curie("omid:ra/06250110138"),
                    ],
                ),
                Author(
                    name="Moretti, Arianna",
                    references=[
                        Reference.from_curie("orcid:0000-0001-5486-7070"),
                        Reference.from_curie("omid:ra/061206532421"),
                    ],
                ),
                Author(
                    name="Peroni, Silvio",
                    references=[
                        Reference.from_curie("orcid:0000-0003-0530-4305"),
                        Reference.from_curie("omid:ra/0614010840729"),
                    ],
                ),
                Author(
                    name="Santini, Cristian",
                    references=[
                        Reference.from_curie("orcid:0000-0001-7363-6737"),
                        Reference.from_curie("omid:ra/067099715"),
                    ],
                ),
                Author(
                    name="Shahidzadeh, Nooshin",
                    references=[
                        Reference.from_curie("orcid:0000-0003-4114-074X"),
                        Reference.from_curie("omid:ra/06220110984"),
                    ],
                ),
            ],
            pub_date=datetime.date(year=2022, month=6, day=1),
            issue="6",
            volume="127",
            venue=Venue(
                name="Scientometrics",
                references=[
                    Reference.from_curie("issn:0138-9130"),
                    Reference.from_curie("issn:1588-2861"),
                    Reference.from_curie("openalex:S148561398"),
                    Reference.from_curie("omid:br/0626055628"),
                ],
            ),
            type="journal article",
            page="3593-3612",
            publisher=Publisher(
                name="Springer Science And Business Media Llc",
                references=[
                    Reference.from_curie("crossref:297"),
                    Reference.from_curie("omid:ra/0610116006"),
                ],
            ),
        )
        self.assertEqual(expected, _process_metadata(data))
