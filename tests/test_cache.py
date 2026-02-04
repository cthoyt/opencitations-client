"""Test the database."""

import unittest

from curies import Reference

from opencitations_client.cache import (
    _get_omid_cache,
    _get_pubmed_cache,
    get_incoming_citations_from_cache,
    get_outgoing_citations_from_cache,
    omid_cache_paths,
    pubmed_cache_paths,
)


@unittest.skipUnless(pubmed_cache_paths.exists(), "can't run tests without cache")
class TestPubmedGraphCache(unittest.TestCase):
    """Tests for the PubMed graph cache."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test case."""
        _get_pubmed_cache()  # warm up the cache, takes 5-10 seconds

    def test_both_ways(self) -> None:
        """Test lookup on a PubMed identifier that's indexed by OpenCitations."""
        # A Novel Combination Therapy Using Rosuvastatin And Lactobacillus
        # Combats Dextran Sodium Sulfate-Induced Colitis In High-Fat Diet-Fed
        # Rats By Targeting The TXNIP/NLRP3 Interaction And Influencing Gut
        # Microbiome Composition
        #
        # see full metadata at https://api.opencitations.net/meta/v1/metadata/pmid:33917884
        example = Reference(prefix="pubmed", identifier="33917884")
        outgoing_citations = get_outgoing_citations_from_cache(example)
        self.assertGreaterEqual(len(outgoing_citations), 50)  # at least 50
        for c in outgoing_citations:
            incoming = get_incoming_citations_from_cache(
                Reference(prefix="pubmed", identifier=c), return_type="str"
            )
            self.assertIn(example.identifier, incoming)

    def test_missing(self) -> None:
        """Test lookup on a PubMed identifier that isn't indexed by OpenCitations."""
        # The Proteomics Standards Initiative Standardized Formats for Spectral
        # Libraries and Fragment Ion Peak Annotations: mzSpecLib and mzPAF
        #
        # see https://pubmed.ncbi.nlm.nih.gov/39514576/
        example = Reference(prefix="pubmed", identifier="39514576")
        self.assertFalse(get_outgoing_citations_from_cache(example))


@unittest.skipUnless(omid_cache_paths.exists(), "can't run tests without cache")
class TestOMIDGraphCache(unittest.TestCase):
    """Tests for the OMID graph cache."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test case."""
        _get_omid_cache()  # warm up the cache, takes 5-10 seconds

    def test_both_ways(self) -> None:
        """Test lookup on a PubMed identifier that's indexed by OpenCitations."""
        # A Novel Combination Therapy Using Rosuvastatin And Lactobacillus
        # Combats Dextran Sodium Sulfate-Induced Colitis In High-Fat Diet-Fed
        # Rats By Targeting The TXNIP/NLRP3 Interaction And Influencing Gut
        # Microbiome Composition
        #
        # see full metadata at https://api.opencitations.net/meta/v1/metadata/omid:br/06180450607
        example_reference = Reference(prefix="omid", identifier="br/06180450607")
        outgoing_citation_references = get_outgoing_citations_from_cache(
            example_reference, return_type="reference"
        )
        self.assertGreaterEqual(len(outgoing_citation_references), 50)  # at least 50
        for outgoing_citation in outgoing_citation_references:
            incoming = get_incoming_citations_from_cache(outgoing_citation, return_type="reference")
            self.assertIn(example_reference, incoming)
