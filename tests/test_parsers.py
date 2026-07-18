"""Parser and extractor tests."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import fitz

from parsers.link_extractor import LinkExtractor
from parsers.pdf_parser import PDFParser


def _make_pdf(path: Path, text: str = "", annotation_urls: list[str] | None = None) -> None:
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    for index, url in enumerate(annotation_urls or []):
        top = 120 + index * 18
        page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(72, top, 260, top + 14), "uri": url})
    document.save(path)
    document.close()


class ParserTests(unittest.TestCase):
    def test_pdf_text_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "resume.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "Jane Doe\nEmail: jane@example.com\nGitHub: https://github.com/janedoe")
            document.save(pdf_path)
            document.close()

            text = PDFParser().extract_text(pdf_path)
            self.assertIn("Jane Doe", text)
            self.assertIn("jane@example.com", text)

    def test_link_extraction_from_visible_pdf_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "resume.pdf"
            _make_pdf(pdf_path, "Visit https://github.com/janedoe and https://portfolio.example.com.")

            text = PDFParser().extract_text(pdf_path).text
            links = LinkExtractor().extract(text)
            self.assertEqual(links, ["https://github.com/janedoe", "https://portfolio.example.com"])

    def test_link_extraction_from_pdf_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "resume.pdf"
            _make_pdf(pdf_path, "GitHub: Aryan27-max", ["https://github.com/Aryan27-max"])

            annotation_links = LinkExtractor().extract_pdf_annotations(pdf_path)
            self.assertEqual(annotation_links, ["https://github.com/Aryan27-max"])

    def test_link_extraction_merges_visible_and_annotation_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "resume.pdf"
            _make_pdf(
                pdf_path,
                "GitHub: Aryan27-max\nPortfolio: aryan.dev",
                ["https://github.com/Aryan27-max", "https://aryan.dev"],
            )

            extractor = LinkExtractor()
            visible_links = extractor.extract(PDFParser().extract_text(pdf_path).text)
            annotation_links = extractor.extract_pdf_annotations(pdf_path)
            self.assertEqual(extractor.merge(visible_links, annotation_links), ["https://github.com/Aryan27-max", "https://aryan.dev"])

    def test_link_extraction_removes_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "resume.pdf"
            _make_pdf(
                pdf_path,
                "https://github.com/janedoe",
                ["https://github.com/janedoe", "https://github.com/janedoe"],
            )

            extractor = LinkExtractor()
            visible_links = extractor.extract(PDFParser().extract_text(pdf_path).text)
            annotation_links = extractor.extract_pdf_annotations(pdf_path)
            self.assertEqual(extractor.merge(visible_links, annotation_links), ["https://github.com/janedoe"])

    def test_link_extraction_ignores_malformed_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "resume.pdf"
            _make_pdf(
                pdf_path,
                "Visit https://github.com/janedoe and javascript:alert(1)",
                ["mailto:aryan@example.com", "https://linkedin.com/in/aryan"],
            )

            extractor = LinkExtractor()
            visible_links = extractor.extract(PDFParser().extract_text(pdf_path).text)
            annotation_links = extractor.extract_pdf_annotations(pdf_path)
            self.assertEqual(extractor.merge(visible_links, annotation_links), ["https://github.com/janedoe", "https://linkedin.com/in/aryan"])

    def test_link_extraction_handles_no_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "resume.pdf"
            _make_pdf(pdf_path, "Jane Doe\nSoftware Engineer")

            extractor = LinkExtractor()
            visible_links = extractor.extract(PDFParser().extract_text(pdf_path).text)
            annotation_links = extractor.extract_pdf_annotations(pdf_path)
            self.assertEqual(extractor.merge(visible_links, annotation_links), [])


if __name__ == "__main__":
    unittest.main()
