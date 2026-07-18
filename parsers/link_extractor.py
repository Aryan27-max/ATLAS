"""URL extraction helpers."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import fitz

_URL_PATTERN = re.compile(r"https?://[^\s<>()\[\]{}\"']+", re.IGNORECASE)


class LinkExtractor:
    """Extract and normalize URLs from resume text."""

    def extract(self, text: str) -> list[str]:
        """Find URLs in plain text while preserving ordering."""

        seen: set[str] = set()
        links: list[str] = []
        for match in _URL_PATTERN.findall(text):
            normalized = self._normalize(match)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            links.append(normalized)
        return links

    def extract_pdf_annotations(self, pdf_path: Path) -> list[str]:
        """Find HTTP(S) URLs embedded as PDF hyperlink annotations."""

        seen: set[str] = set()
        links: list[str] = []
        document = None
        try:
            document = fitz.open(pdf_path)
            for page in document:
                for link in page.get_links():
                    normalized = self._normalize(str(link.get("uri") or ""))
                    if not normalized or normalized in seen:
                        continue
                    seen.add(normalized)
                    links.append(normalized)
        except Exception:
            return []
        finally:
            if document is not None:
                document.close()
        return links

    def merge(self, *url_groups: list[str]) -> list[str]:
        """Merge URL groups while preserving order and removing duplicates."""

        seen: set[str] = set()
        merged: list[str] = []
        for group in url_groups:
            for url in group:
                normalized = self._normalize(url)
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                merged.append(normalized)
        return merged

    def _normalize(self, url: str) -> str:
        url = url.rstrip(".,);]")
        parsed = urlparse(url)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            return ""
        return url
