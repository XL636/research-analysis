"""External academic search providers for citation collection."""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path

import httpx
import yaml
from loguru import logger
from pydantic import BaseModel, Field


# --- Config / Result Models ---


class SearchProviderConfig(BaseModel):
    """Configuration for a single search provider."""

    name: str = ""
    base_url: str = ""
    api_key_env: str = ""
    enabled: bool = True
    timeout: int = 10
    max_results: int = 5


class ExternalSearchResult(BaseModel):
    """A single result from an external academic search."""

    title: str = ""
    authors: str = ""
    year: str = ""
    venue: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    source: str = ""  # "semantic_scholar" | "openalex" | "arxiv" | "pubmed" | "biorxiv" | "medrxiv" | "crossref"


# --- Provider ABC ---


class SearchProvider(ABC):
    """Abstract base for academic search providers."""

    def __init__(self, config: SearchProviderConfig) -> None:
        self.config = config
        self._client = httpx.Client(timeout=config.timeout)

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def is_available(self) -> bool:
        """Provider is available if enabled AND (no key needed OR key is set)."""
        if not self.config.enabled:
            return False
        if not self.config.api_key_env:
            return True
        # S2 and OpenAlex work without key (just lower limits), so always available when enabled
        return True

    @property
    def has_api_key(self) -> bool:
        if not self.config.api_key_env:
            return False
        return bool(os.environ.get(self.config.api_key_env, ""))

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[ExternalSearchResult]:
        ...

    def close(self) -> None:
        self._client.close()


# --- Semantic Scholar ---


class SemanticScholarProvider(SearchProvider):
    """Semantic Scholar Academic Graph API."""

    def search(self, query: str, max_results: int = 5) -> list[ExternalSearchResult]:
        try:
            headers: dict[str, str] = {}
            api_key = os.environ.get(self.config.api_key_env or "", "")
            if api_key:
                headers["x-api-key"] = api_key

            resp = self._client.get(
                f"{self.config.base_url}/paper/search",
                params={
                    "query": query,
                    "fields": "title,authors,year,venue,abstract,externalIds,openAccessPdf",
                    "limit": min(max_results, self.config.max_results),
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            results: list[ExternalSearchResult] = []
            for paper in data.get("data", []):
                if not paper:
                    continue
                authors_list = paper.get("authors") or []
                author_str = ", ".join(a.get("name", "") for a in authors_list[:5])
                if len(authors_list) > 5:
                    author_str += " et al."

                ext_ids = paper.get("externalIds") or {}
                doi = ext_ids.get("DOI", "")
                arxiv_id = ext_ids.get("ArXiv", "")

                # Prefer direct OA PDF URL from Semantic Scholar
                oa_pdf = paper.get("openAccessPdf") or {}
                pdf_url = oa_pdf.get("url", "")

                # Fallback to arxiv or DOI URL
                url = pdf_url or ""
                if not url and arxiv_id:
                    url = f"https://arxiv.org/abs/{arxiv_id}"
                if not url and doi:
                    url = f"https://doi.org/{doi}"

                results.append(ExternalSearchResult(
                    title=paper.get("title", ""),
                    authors=author_str,
                    year=str(paper.get("year", "")),
                    venue=paper.get("venue", "") or "",
                    doi=doi,
                    url=url,
                    abstract=(paper.get("abstract") or "")[:500],
                    source="semantic_scholar",
                ))
            return results

        except Exception as e:
            logger.warning(f"Semantic Scholar search failed for '{query}': {e}")
            return []


# --- OpenAlex ---


class OpenAlexProvider(SearchProvider):
    """OpenAlex API."""

    def _rebuild_abstract(self, inverted_index: dict | None) -> str:
        """Rebuild abstract from OpenAlex inverted index format."""
        if not inverted_index:
            return ""
        word_positions: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in word_positions)[:500]

    def search(self, query: str, max_results: int = 5) -> list[ExternalSearchResult]:
        try:
            headers: dict[str, str] = {}
            email = os.environ.get(self.config.api_key_env or "", "")
            if email:
                headers["User-Agent"] = f"research-analysis/0.1 (mailto:{email})"

            resp = self._client.get(
                f"{self.config.base_url}/works",
                params={
                    "search": query,
                    "per_page": min(max_results, self.config.max_results),
                    "select": "id,title,authorships,publication_year,primary_location,doi,abstract_inverted_index,open_access,best_oa_url",
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            results: list[ExternalSearchResult] = []
            for work in data.get("results", []):
                if not work:
                    continue
                authorships = work.get("authorships") or []
                author_names = []
                for a in authorships[:5]:
                    author_info = a.get("author") or {}
                    name = author_info.get("display_name", "")
                    if name:
                        author_names.append(name)
                author_str = ", ".join(author_names)
                if len(authorships) > 5:
                    author_str += " et al."

                doi = work.get("doi", "") or ""
                if doi and doi.startswith("https://doi.org/"):
                    doi = doi[len("https://doi.org/"):]

                year = work.get("publication_year")
                venue = ""
                primary_location = work.get("primary_location") or {}
                source = primary_location.get("source") or {}
                if source:
                    venue = source.get("display_name", "")

                abstract = self._rebuild_abstract(
                    work.get("abstract_inverted_index")
                )

                # Prefer OA PDF URL from OpenAlex
                oa_info = work.get("open_access") or {}
                oa_url = oa_info.get("oa_url", "") or ""
                url = oa_url if oa_url else (work.get("doi", "") or "")

                results.append(ExternalSearchResult(
                    title=work.get("title", "") or "",
                    authors=author_str,
                    year=str(year) if year else "",
                    venue=venue,
                    doi=doi,
                    url=url,
                    abstract=abstract,
                    source="openalex",
                ))
            return results

        except Exception as e:
            logger.warning(f"OpenAlex search failed for '{query}': {e}")
            return []


# --- arXiv ---

_ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
}


class ArxivProvider(SearchProvider):
    """arXiv search API (Atom XML)."""

    def search(self, query: str, max_results: int = 5) -> list[ExternalSearchResult]:
        try:
            resp = self._client.get(
                f"{self.config.base_url}/query",
                params={
                    "search_query": f"all:{query}",
                    "max_results": min(max_results, self.config.max_results),
                    "sortBy": "relevance",
                },
            )
            resp.raise_for_status()

            root = ET.fromstring(resp.text)
            results: list[ExternalSearchResult] = []

            for entry in root.findall("atom:entry", _ARXIV_NS):
                title_el = entry.find("atom:title", _ARXIV_NS)
                title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""

                authors_els = entry.findall("atom:author/atom:name", _ARXIV_NS)
                author_names = [a.text.strip() for a in authors_els[:5] if a.text]
                author_str = ", ".join(author_names)
                if len(authors_els) > 5:
                    author_str += " et al."

                summary_el = entry.find("atom:summary", _ARXIV_NS)
                abstract = (summary_el.text or "").strip().replace("\n", " ")[:500] if summary_el is not None else ""

                published_el = entry.find("atom:published", _ARXIV_NS)
                year = ""
                if published_el is not None and published_el.text:
                    year = published_el.text[:4]

                # Get the arxiv abs link
                url = ""
                for link in entry.findall("atom:link", _ARXIV_NS):
                    if link.get("type") == "text/html":
                        url = link.get("href", "")
                        break
                if not url:
                    id_el = entry.find("atom:id", _ARXIV_NS)
                    if id_el is not None and id_el.text:
                        url = id_el.text

                results.append(ExternalSearchResult(
                    title=title,
                    authors=author_str,
                    year=year,
                    venue="arXiv",
                    doi="",
                    url=url,
                    abstract=abstract,
                    source="arxiv",
                ))
            return results

        except Exception as e:
            logger.warning(f"arXiv search failed for '{query}': {e}")
            return []


# --- PubMed ---


class PubMedProvider(SearchProvider):
    """PubMed via NCBI E-utilities (esearch + efetch)."""

    def search(self, query: str, max_results: int = 5) -> list[ExternalSearchResult]:
        try:
            limit = min(max_results, self.config.max_results)
            params: dict[str, str | int] = {
                "db": "pubmed",
                "term": query,
                "retmax": limit,
                "retmode": "json",
                "sort": "relevance",
            }
            api_key = os.environ.get(self.config.api_key_env or "", "")
            if api_key:
                params["api_key"] = api_key

            # Step 1: esearch to get PMIDs
            resp = self._client.get(
                f"{self.config.base_url}/esearch.fcgi",
                params=params,
            )
            resp.raise_for_status()
            search_data = resp.json()
            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return []

            # Step 2: efetch to get metadata XML
            fetch_params: dict[str, str] = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
            }
            if api_key:
                fetch_params["api_key"] = api_key

            resp2 = self._client.get(
                f"{self.config.base_url}/efetch.fcgi",
                params=fetch_params,
            )
            resp2.raise_for_status()

            root = ET.fromstring(resp2.text)
            results: list[ExternalSearchResult] = []

            for article_el in root.findall(".//PubmedArticle"):
                medline = article_el.find("MedlineCitation")
                if medline is None:
                    continue
                art = medline.find("Article")
                if art is None:
                    continue

                # Title
                title_el = art.find("ArticleTitle")
                title = (title_el.text or "").strip() if title_el is not None else ""

                # Authors
                author_list = art.findall("AuthorList/Author")
                author_names: list[str] = []
                for a in author_list[:5]:
                    last = a.findtext("LastName", "")
                    fore = a.findtext("ForeName", "")
                    if last:
                        author_names.append(f"{last} {fore}".strip())
                author_str = ", ".join(author_names)
                if len(author_list) > 5:
                    author_str += " et al."

                # Abstract
                abstract_parts: list[str] = []
                for abs_text in art.findall("Abstract/AbstractText"):
                    if abs_text.text:
                        abstract_parts.append(abs_text.text.strip())
                abstract = " ".join(abstract_parts)[:500]

                # Journal / Year
                journal_el = art.find("Journal")
                journal = ""
                year = ""
                if journal_el is not None:
                    journal = journal_el.findtext("Title", "") or journal_el.findtext("ISOAbbreviation", "")
                    ji = journal_el.find("JournalIssue")
                    if ji is not None:
                        pub_date = ji.find("PubDate")
                        if pub_date is not None:
                            year = pub_date.findtext("Year", "")

                # DOI
                doi = ""
                for eid in art.findall("ELocationID"):
                    if eid.get("EIdType") == "doi":
                        doi = (eid.text or "").strip()
                        break

                # PMID
                pmid_el = medline.find("PMID")
                pmid = (pmid_el.text or "").strip() if pmid_el is not None else ""
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
                if not url and doi:
                    url = f"https://doi.org/{doi}"

                results.append(ExternalSearchResult(
                    title=title,
                    authors=author_str,
                    year=year,
                    venue=journal,
                    doi=doi,
                    url=url,
                    abstract=abstract,
                    source="pubmed",
                ))
            return results

        except Exception as e:
            logger.warning(f"PubMed search failed for '{query}': {e}")
            return []


# --- bioRxiv / medRxiv (via Europe PMC) ---


class BiorxivProvider(SearchProvider):
    """bioRxiv + medRxiv via Europe PMC REST API."""

    def search(self, query: str, max_results: int = 5) -> list[ExternalSearchResult]:
        try:
            limit = min(max_results, self.config.max_results)
            # SRC:PPR filters for preprints (bioRxiv + medRxiv)
            resp = self._client.get(
                f"{self.config.base_url}/search",
                params={
                    "query": f"(SRC:PPR) AND ({query})",
                    "resultType": "core",
                    "pageSize": limit,
                    "format": "json",
                    "sort": "RELEVANCE",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            result_list = data.get("resultList", {}).get("result", [])
            results: list[ExternalSearchResult] = []

            for item in result_list:
                title = (item.get("title") or "").strip()
                if not title:
                    continue

                # Authors
                author_str = item.get("authorString", "")
                if author_str:
                    parts = [a.strip() for a in author_str.split(",")]
                    if len(parts) > 5:
                        author_str = ", ".join(parts[:5]) + " et al."

                year = str(item.get("pubYear", ""))
                doi = item.get("doi", "") or ""

                # Distinguish bioRxiv vs medRxiv by bookOrReportDetails or publisher
                publisher = (item.get("bookOrReportDetails", {}) or {}).get("publisher", "")
                if not publisher:
                    publisher = item.get("publisherName", "") or ""
                if "medrxiv" in publisher.lower():
                    venue = "medRxiv"
                    source = "medrxiv"
                else:
                    venue = "bioRxiv"
                    source = "biorxiv"

                abstract = (item.get("abstractText") or "").strip()[:500]

                url = ""
                if doi:
                    url = f"https://doi.org/{doi}"

                results.append(ExternalSearchResult(
                    title=title,
                    authors=author_str,
                    year=year,
                    venue=venue,
                    doi=doi,
                    url=url,
                    abstract=abstract,
                    source=source,
                ))
            return results

        except Exception as e:
            logger.warning(f"bioRxiv/medRxiv search failed for '{query}': {e}")
            return []


# --- CrossRef ---


class CrossRefProvider(SearchProvider):
    """CrossRef API — free, covers DOI-registered papers including Chinese journals."""

    def search(self, query: str, max_results: int = 5) -> list[ExternalSearchResult]:
        try:
            limit = min(max_results, self.config.max_results)
            headers: dict[str, str] = {}
            email = os.environ.get(self.config.api_key_env or "", "")
            params: dict[str, str | int] = {
                "query": query,
                "rows": limit,
                "select": "title,author,published,container-title,DOI,URL,abstract",
            }
            if email:
                params["mailto"] = email
                headers["User-Agent"] = f"research-analysis/0.1 (mailto:{email})"

            resp = self._client.get(
                f"{self.config.base_url}/works",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("message", {}).get("items", [])
            results: list[ExternalSearchResult] = []

            for item in items:
                # Title
                title_list = item.get("title") or []
                title = title_list[0] if title_list else ""

                # Authors
                author_list = item.get("author") or []
                author_names = []
                for a in author_list[:5]:
                    family = a.get("family", "")
                    given = a.get("given", "")
                    if family:
                        author_names.append(f"{family} {given}".strip())
                author_str = ", ".join(author_names)
                if len(author_list) > 5:
                    author_str += " et al."

                # Year
                published = item.get("published") or item.get("published-print") or item.get("published-online") or {}
                date_parts = published.get("date-parts", [[]])
                year_val = date_parts[0][0] if date_parts and date_parts[0] else None
                year = str(year_val) if year_val and isinstance(year_val, int) else ""

                # Venue
                container = item.get("container-title") or []
                venue = container[0] if container else ""

                # DOI & URL
                doi = item.get("DOI", "") or ""
                url = item.get("URL", "") or ""
                if not url and doi:
                    url = f"https://doi.org/{doi}"

                # Abstract — may contain JATS XML tags
                raw_abstract = item.get("abstract", "") or ""
                abstract = re.sub(r"<[^>]+>", "", raw_abstract).strip()[:500]

                if not title:
                    continue

                results.append(ExternalSearchResult(
                    title=title,
                    authors=author_str,
                    year=year,
                    venue=venue,
                    doi=doi,
                    url=url,
                    abstract=abstract,
                    source="crossref",
                ))
            return results

        except Exception as e:
            logger.warning(f"CrossRef search failed for '{query}': {e}")
            return []


# --- SearchManager (aggregator) ---

_CONFIG_PATH = Path("config/settings.yaml")

_PROVIDER_CLASSES: dict[str, type[SearchProvider]] = {
    "semantic_scholar": SemanticScholarProvider,
    "openalex": OpenAlexProvider,
    "arxiv": ArxivProvider,
    "pubmed": PubMedProvider,
    "biorxiv": BiorxivProvider,
    "crossref": CrossRefProvider,
}


class SearchManager:
    """Aggregates multiple search providers and deduplicates results."""

    def __init__(self) -> None:
        self._providers: list[SearchProvider] = []
        self._load_config()

    def _load_config(self) -> None:
        """Load search provider configs from settings.yaml."""
        if not _CONFIG_PATH.exists():
            return
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            providers_conf = config.get("search_providers", {})
            for name, conf in providers_conf.items():
                cls = _PROVIDER_CLASSES.get(name)
                if not cls:
                    continue
                provider_config = SearchProviderConfig(name=name, **conf)
                provider = cls(provider_config)
                if provider.is_available:
                    self._providers.append(provider)
        except Exception:
            logger.warning("Failed to load search provider config", exc_info=True)

    @property
    def has_providers(self) -> bool:
        return len(self._providers) > 0

    @property
    def available_providers(self) -> list[SearchProvider]:
        return list(self._providers)

    def search(
        self,
        query: str,
        max_results: int = 5,
        provider_names: list[str] | None = None,
    ) -> list[ExternalSearchResult]:
        """Search available providers and deduplicate by title.

        Args:
            query: Search query string.
            max_results: Max results per provider.
            provider_names: Optional list of provider names to use (e.g. ["arxiv", "pubmed"]).
                           If None, all available providers are used.
        """
        all_results: list[ExternalSearchResult] = []
        seen_titles: set[str] = set()

        providers = self._providers
        if provider_names:
            name_set = {n.lower() for n in provider_names}
            providers = [p for p in self._providers if p.name in name_set]

        for provider in providers:
            try:
                results = provider.search(query, max_results=max_results)
                for r in results:
                    title_key = r.title.lower().strip()
                    if title_key and title_key not in seen_titles:
                        seen_titles.add(title_key)
                        all_results.append(r)
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")

        return all_results

    def get_provider_status(self) -> list[dict]:
        """Get status of all configured providers (for Settings API)."""
        if not _CONFIG_PATH.exists():
            return []
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            providers_conf = config.get("search_providers", {})
        except Exception:
            logger.warning("Search config load failed", exc_info=True)
            return []

        statuses = []
        for name, conf in providers_conf.items():
            api_key_env = conf.get("api_key_env", "")
            current_key = os.environ.get(api_key_env, "") if api_key_env else ""
            configured = bool(current_key)
            masked = f"****{current_key[-4:]}" if len(current_key) >= 4 else ""

            statuses.append({
                "name": name,
                "enabled": conf.get("enabled", True),
                "api_key_env": api_key_env,
                "api_key_configured": configured,
                "masked_key": masked,
            })
        return statuses

    def close(self) -> None:
        for p in self._providers:
            p.close()
