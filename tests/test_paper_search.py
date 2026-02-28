"""Tests for paper search providers and SearchManager enhancements."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

import pytest

from src.core.search_client import (
    BiorxivProvider,
    ExternalSearchResult,
    PubMedProvider,
    SearchManager,
    SearchProviderConfig,
)


# --- PubMed Provider ---


PUBMED_ESEARCH_RESPONSE = {
    "esearchresult": {
        "idlist": ["12345678", "87654321"]
    }
}

PUBMED_EFETCH_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Deep Learning for Medical Imaging</ArticleTitle>
        <AuthorList>
          <Author><LastName>Zhang</LastName><ForeName>Wei</ForeName></Author>
          <Author><LastName>Li</LastName><ForeName>Ming</ForeName></Author>
          <Author><LastName>Wang</LastName><ForeName>Jun</ForeName></Author>
          <Author><LastName>Chen</LastName><ForeName>Xiao</ForeName></Author>
          <Author><LastName>Liu</LastName><ForeName>Yang</ForeName></Author>
          <Author><LastName>Wu</LastName><ForeName>Fei</ForeName></Author>
        </AuthorList>
        <Abstract>
          <AbstractText>This paper presents a novel approach to medical imaging using deep learning.</AbstractText>
        </Abstract>
        <Journal>
          <ISOAbbreviation>Nature Med</ISOAbbreviation>
          <Title>Nature Medicine</Title>
          <JournalIssue>
            <PubDate><Year>2024</Year></PubDate>
          </JournalIssue>
        </Journal>
        <ELocationID EIdType="doi">10.1038/s41591-024-001</ELocationID>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>87654321</PMID>
      <Article>
        <ArticleTitle>Transformer Models in NLP</ArticleTitle>
        <AuthorList>
          <Author><LastName>Smith</LastName><ForeName>John</ForeName></Author>
        </AuthorList>
        <Abstract>
          <AbstractText>A review of transformer architectures.</AbstractText>
        </Abstract>
        <Journal>
          <Title>ACL Proceedings</Title>
          <JournalIssue>
            <PubDate><Year>2023</Year></PubDate>
          </JournalIssue>
        </Journal>
        <ELocationID EIdType="pii">S0001-2345(23)00001</ELocationID>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


class TestPubMedProvider:
    def _make_provider(self) -> PubMedProvider:
        config = SearchProviderConfig(
            name="pubmed",
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            api_key_env="",
            enabled=True,
            timeout=10,
            max_results=5,
        )
        return PubMedProvider(config)

    def test_search_parses_results(self):
        provider = self._make_provider()

        mock_esearch = MagicMock()
        mock_esearch.json.return_value = PUBMED_ESEARCH_RESPONSE
        mock_esearch.raise_for_status = MagicMock()

        mock_efetch = MagicMock()
        mock_efetch.text = PUBMED_EFETCH_XML
        mock_efetch.raise_for_status = MagicMock()

        provider._client.get = MagicMock(side_effect=[mock_esearch, mock_efetch])

        results = provider.search("deep learning", max_results=5)

        assert len(results) == 2
        assert results[0].title == "Deep Learning for Medical Imaging"
        assert results[0].source == "pubmed"
        assert results[0].year == "2024"
        assert results[0].doi == "10.1038/s41591-024-001"
        assert "Zhang Wei" in results[0].authors
        assert "et al." in results[0].authors  # >5 authors
        assert results[0].url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        assert results[0].venue == "Nature Medicine"

    def test_search_second_paper_no_doi(self):
        provider = self._make_provider()

        mock_esearch = MagicMock()
        mock_esearch.json.return_value = PUBMED_ESEARCH_RESPONSE
        mock_esearch.raise_for_status = MagicMock()

        mock_efetch = MagicMock()
        mock_efetch.text = PUBMED_EFETCH_XML
        mock_efetch.raise_for_status = MagicMock()

        provider._client.get = MagicMock(side_effect=[mock_esearch, mock_efetch])

        results = provider.search("transformer", max_results=5)

        # Second paper has ELocationID with type "pii" not "doi"
        assert results[1].doi == ""
        assert results[1].url == "https://pubmed.ncbi.nlm.nih.gov/87654321/"

    def test_search_empty_results(self):
        provider = self._make_provider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"esearchresult": {"idlist": []}}
        mock_resp.raise_for_status = MagicMock()

        provider._client.get = MagicMock(return_value=mock_resp)

        results = provider.search("nonexistent query")
        assert results == []

    def test_search_handles_error(self):
        provider = self._make_provider()
        provider._client.get = MagicMock(side_effect=Exception("Network error"))

        results = provider.search("test")
        assert results == []


# --- BioRxiv Provider ---


EUROPEPMC_RESPONSE = {
    "resultList": {
        "result": [
            {
                "title": "CRISPR Gene Editing in Neurons",
                "authorString": "Smith J, Lee K, Wang L, Chen M, Park S, Kim H",
                "pubYear": "2024",
                "doi": "10.1101/2024.01.01.001",
                "abstractText": "A new CRISPR approach for neural editing.",
                "bookOrReportDetails": {"publisher": "bioRxiv"},
                "publisherName": "",
            },
            {
                "title": "COVID-19 Vaccine Efficacy Meta-analysis",
                "authorString": "Johnson A, Brown B",
                "pubYear": "2023",
                "doi": "10.1101/2023.06.15.002",
                "abstractText": "Meta-analysis of vaccine trials.",
                "bookOrReportDetails": {"publisher": "medRxiv"},
                "publisherName": "",
            },
            {
                "title": "",  # Empty title should be skipped
                "authorString": "Nobody",
                "pubYear": "2024",
                "doi": "",
                "abstractText": "",
                "bookOrReportDetails": None,
                "publisherName": "",
            },
        ]
    }
}


class TestBiorxivProvider:
    def _make_provider(self) -> BiorxivProvider:
        config = SearchProviderConfig(
            name="biorxiv",
            base_url="https://www.ebi.ac.uk/europepmc/webservices/rest",
            api_key_env="",
            enabled=True,
            timeout=15,
            max_results=5,
        )
        return BiorxivProvider(config)

    def test_search_parses_results(self):
        provider = self._make_provider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = EUROPEPMC_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        provider._client.get = MagicMock(return_value=mock_resp)

        results = provider.search("CRISPR", max_results=5)

        # Empty title entry should be skipped
        assert len(results) == 2

        # First result: bioRxiv
        assert results[0].title == "CRISPR Gene Editing in Neurons"
        assert results[0].source == "biorxiv"
        assert results[0].venue == "bioRxiv"
        assert results[0].year == "2024"
        assert results[0].doi == "10.1101/2024.01.01.001"
        assert results[0].url == "https://doi.org/10.1101/2024.01.01.001"

    def test_search_distinguishes_medrxiv(self):
        provider = self._make_provider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = EUROPEPMC_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        provider._client.get = MagicMock(return_value=mock_resp)

        results = provider.search("COVID", max_results=5)

        # Second result: medRxiv
        assert results[1].source == "medrxiv"
        assert results[1].venue == "medRxiv"

    def test_search_truncates_authors(self):
        provider = self._make_provider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = EUROPEPMC_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        provider._client.get = MagicMock(return_value=mock_resp)

        results = provider.search("test", max_results=5)

        # First paper has 6 authors, should truncate to 5 + et al.
        assert "et al." in results[0].authors

    def test_search_handles_error(self):
        provider = self._make_provider()
        provider._client.get = MagicMock(side_effect=Exception("Timeout"))

        results = provider.search("test")
        assert results == []

    def test_search_empty_result_list(self):
        provider = self._make_provider()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"resultList": {"result": []}}
        mock_resp.raise_for_status = MagicMock()

        provider._client.get = MagicMock(return_value=mock_resp)

        results = provider.search("nothing")
        assert results == []


# --- SearchManager provider_names filtering ---


class TestSearchManagerFiltering:
    @patch("src.core.search_client._CONFIG_PATH")
    def test_search_with_provider_names_filter(self, mock_path):
        """SearchManager.search(provider_names=...) should only use matching providers."""
        sm = SearchManager.__new__(SearchManager)
        sm._providers = []

        # Create mock providers
        mock_arxiv = MagicMock()
        mock_arxiv.name = "arxiv"
        mock_arxiv.search.return_value = [
            ExternalSearchResult(title="arXiv Paper", source="arxiv")
        ]

        mock_pubmed = MagicMock()
        mock_pubmed.name = "pubmed"
        mock_pubmed.search.return_value = [
            ExternalSearchResult(title="PubMed Paper", source="pubmed")
        ]

        mock_biorxiv = MagicMock()
        mock_biorxiv.name = "biorxiv"
        mock_biorxiv.search.return_value = [
            ExternalSearchResult(title="bioRxiv Paper", source="biorxiv")
        ]

        sm._providers = [mock_arxiv, mock_pubmed, mock_biorxiv]

        # Filter to only pubmed
        results = sm.search("test", provider_names=["pubmed"])
        assert len(results) == 1
        assert results[0].source == "pubmed"
        mock_arxiv.search.assert_not_called()
        mock_biorxiv.search.assert_not_called()

    @patch("src.core.search_client._CONFIG_PATH")
    def test_search_no_filter_uses_all(self, mock_path):
        """SearchManager.search() without provider_names should use all providers."""
        sm = SearchManager.__new__(SearchManager)
        sm._providers = []

        mock_p1 = MagicMock()
        mock_p1.name = "arxiv"
        mock_p1.search.return_value = [
            ExternalSearchResult(title="Paper A", source="arxiv")
        ]
        mock_p2 = MagicMock()
        mock_p2.name = "pubmed"
        mock_p2.search.return_value = [
            ExternalSearchResult(title="Paper B", source="pubmed")
        ]

        sm._providers = [mock_p1, mock_p2]

        results = sm.search("test")
        assert len(results) == 2
        mock_p1.search.assert_called_once()
        mock_p2.search.assert_called_once()

    @patch("src.core.search_client._CONFIG_PATH")
    def test_search_deduplicates_by_title(self, mock_path):
        """Results with same title from different providers should be deduplicated."""
        sm = SearchManager.__new__(SearchManager)

        mock_p1 = MagicMock()
        mock_p1.name = "arxiv"
        mock_p1.search.return_value = [
            ExternalSearchResult(title="Same Paper", source="arxiv")
        ]
        mock_p2 = MagicMock()
        mock_p2.name = "pubmed"
        mock_p2.search.return_value = [
            ExternalSearchResult(title="Same Paper", source="pubmed")
        ]

        sm._providers = [mock_p1, mock_p2]

        results = sm.search("test")
        assert len(results) == 1  # Deduplicated

    @patch("src.core.search_client._CONFIG_PATH")
    def test_provider_names_case_insensitive(self, mock_path):
        """provider_names filter should be case-insensitive."""
        sm = SearchManager.__new__(SearchManager)

        mock_p = MagicMock()
        mock_p.name = "pubmed"
        mock_p.search.return_value = [
            ExternalSearchResult(title="Paper", source="pubmed")
        ]

        sm._providers = [mock_p]

        # Use uppercase in filter
        results = sm.search("test", provider_names=["PubMed"])
        # BUG CHECK: the current code does `n.lower()` on provider_names
        # but compares against `p.name` which is already lowercase.
        # This should work if the code lowercases the filter names.
        assert len(results) == 1


# --- CLI paper-search command ---


class TestPaperSearchCLI:
    def test_paper_search_command_exists(self):
        """The paper-search command should be registered."""
        from typer.testing import CliRunner
        from main import app

        runner = CliRunner()
        result = runner.invoke(app, ["paper-search", "--help"])
        assert result.exit_code == 0
        assert "搜索外部学术论文" in result.output or "paper-search" in result.output.lower()

    @patch("src.core.search_client.SearchManager")
    def test_paper_search_no_results(self, MockSM):
        from typer.testing import CliRunner
        from main import app

        mock_sm = MockSM.return_value
        mock_sm.has_providers = True
        mock_sm.search.return_value = []

        runner = CliRunner()
        result = runner.invoke(app, ["paper-search", "nonexistent"])
        assert result.exit_code == 0

    @patch("src.core.search_client.SearchManager")
    def test_paper_search_with_results(self, MockSM):
        from typer.testing import CliRunner
        from main import app

        mock_sm = MockSM.return_value
        mock_sm.has_providers = True
        mock_sm.search.return_value = [
            ExternalSearchResult(
                title="Test Paper",
                authors="Author A",
                year="2024",
                venue="Nature",
                doi="10.1000/test",
                url="https://example.com",
                abstract="Test abstract",
                source="pubmed",
            )
        ]

        runner = CliRunner()
        result = runner.invoke(app, ["paper-search", "test"])
        assert result.exit_code == 0
        assert "Test Paper" in result.output

    @patch("src.core.search_client.SearchManager")
    def test_paper_search_json_output(self, MockSM):
        from typer.testing import CliRunner
        from main import app
        import json

        mock_sm = MockSM.return_value
        mock_sm.has_providers = True
        mock_sm.search.return_value = [
            ExternalSearchResult(
                title="JSON Paper",
                source="arxiv",
            )
        ]

        runner = CliRunner()
        result = runner.invoke(app, ["paper-search", "test", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["title"] == "JSON Paper"

    @patch("src.core.search_client.SearchManager")
    def test_paper_search_providers_param(self, MockSM):
        """--providers should be passed to SearchManager.search()."""
        from typer.testing import CliRunner
        from main import app

        mock_sm = MockSM.return_value
        mock_sm.has_providers = True
        mock_sm.search.return_value = []

        runner = CliRunner()
        result = runner.invoke(app, ["paper-search", "test", "--providers", "arxiv,pubmed"])
        assert result.exit_code == 0

        # Check that provider_names was passed
        mock_sm.search.assert_called_once()
        call_kwargs = mock_sm.search.call_args
        # Should have provider_names=["arxiv", "pubmed"]
        assert call_kwargs[1].get("provider_names") == ["arxiv", "pubmed"] or \
               (len(call_kwargs[0]) >= 3 and call_kwargs[0][2] == ["arxiv", "pubmed"])


# --- Provider registration ---


class TestProviderRegistration:
    def test_pubmed_registered(self):
        from src.core.search_client import _PROVIDER_CLASSES
        assert "pubmed" in _PROVIDER_CLASSES
        assert _PROVIDER_CLASSES["pubmed"] is PubMedProvider

    def test_biorxiv_registered(self):
        from src.core.search_client import _PROVIDER_CLASSES
        assert "biorxiv" in _PROVIDER_CLASSES
        assert _PROVIDER_CLASSES["biorxiv"] is BiorxivProvider

    def test_all_five_providers_registered(self):
        from src.core.search_client import _PROVIDER_CLASSES
        expected = {"semantic_scholar", "openalex", "arxiv", "pubmed", "biorxiv"}
        assert set(_PROVIDER_CLASSES.keys()) == expected
