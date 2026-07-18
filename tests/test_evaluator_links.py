"""Evaluator link extraction tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import fitz

from agents.evaluator import CandidateEvaluator
from config import AtlasConfig


def _make_pdf(path: Path, text: str, annotation_urls: list[str]) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    for index, url in enumerate(annotation_urls):
        top = 120 + index * 18
        page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(72, top, 260, top + 14), "uri": url})
    document.save(path)
    document.close()


class EvaluatorLinkTests(unittest.TestCase):
    def test_candidate_profile_keeps_all_discovered_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "resume.pdf"
            _make_pdf(
                pdf_path,
                "GitHub: https://github.com/janedoe",
                ["https://linkedin.com/in/janedoe", "https://janedoe.dev"],
            )

            config = AtlasConfig()
            evaluator = CandidateEvaluator(config=config, ollama=MagicMock(), logger=MagicMock(), internet_available=False)
            profile = evaluator.build_profile(pdf_path)

            self.assertEqual(profile.links.all_urls, ["https://github.com/janedoe", "https://linkedin.com/in/janedoe", "https://janedoe.dev"])
            self.assertEqual(profile.links.github_url, "https://github.com/janedoe")
            self.assertEqual(profile.links.linkedin_url, "https://linkedin.com/in/janedoe")
            self.assertEqual(profile.links.portfolio_url, "https://janedoe.dev")
            evaluator.logger.info.assert_any_call(
                "Link extraction for %s | visible=%s | annotations=%s | final=%s",
                "resume.pdf",
                1,
                2,
                3,
            )


if __name__ == "__main__":
    unittest.main()
