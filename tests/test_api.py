"""Trivial version test."""

import unittest

from curies import Reference

from opencitations_client import get_incoming_citations
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
