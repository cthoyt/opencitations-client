"""Test the database."""

import unittest

from opencitations_client.db import (
    _get_cache,
    get_incoming_citations,
    get_outgoing_citations,
    paths,
)


@unittest.skipUnless(paths.exists(), "can't run tests without cache")
class TestPubmedGraphCache(unittest.TestCase):
    """Tests for the PubMed graph cache."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test case."""
        _get_cache()  # warm up the cache, takes 5-10 seconds

    def test_both_ways(self) -> None:
        """Test lookup on a PubMed identifier that's indexed by OpenCitations."""
        # A Novel Combination Therapy Using Rosuvastatin And Lactobacillus
        # Combats Dextran Sodium Sulfate-Induced Colitis In High-Fat Diet-Fed
        # Rats By Targeting The TXNIP/NLRP3 Interaction And Influencing Gut
        # Microbiome Composition
        #
        # see full metadata at https://api.opencitations.net/meta/v1/metadata/pmid:33917884
        example = "33917884"
        outgoing_citations = get_outgoing_citations(example)
        self.assertGreaterEqual(5, len(outgoing_citations))
        for c in outgoing_citations:
            incoming = get_incoming_citations(c)
            self.assertIn(example, incoming)

    def test_missing(self) -> None:
        """Test lookup on a PubMed identifier that isn't indexed by OpenCitations."""
        # The Proteomics Standards Initiative Standardized Formats for Spectral
        # Libraries and Fragment Ion Peak Annotations: mzSpecLib and mzPAF
        #
        # see https://pubmed.ncbi.nlm.nih.gov/39514576/
        example = "39514576"
        self.assertFalse(get_outgoing_citations(example))
