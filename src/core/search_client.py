"""External academic search providers for citation collection."""

from __future__ import annotations

import os
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
    source: str = ""  # "semantic_scholar" | "openalex" | "arxiv"


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


# --- SearchManager (aggregator) ---

_CONFIG_PATH = Path("config/settings.yaml")

_PROVIDER_CLASSES: dict[str, type[SearchProvider]] = {
    "semantic_scholar": SemanticScholarProvider,
    "openalex": OpenAlexProvider,
    "arxiv": ArxivProvider,
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
        except Exception as e:
            logger.warning(f"Failed to load search provider config: {e}")

    @property
    def has_providers(self) -> bool:
        return len(self._providers) > 0

    @property
    def available_providers(self) -> list[SearchProvider]:
        return list(self._providers)

    def search(self, query: str, max_results: int = 5) -> list[ExternalSearchResult]:
        """Search all available providers and deduplicate by title."""
        all_results: list[ExternalSearchResult] = []
        seen_titles: set[str] = set()

        for provider in self._providers:
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
