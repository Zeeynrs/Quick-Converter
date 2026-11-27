import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quick_convert.paths import (
    normalize_file_input,
    normalize_merged_filename,
    plan_batch_actions,
    unique_dir_path,
    unique_output_path,
)


class TestPaths(unittest.TestCase):
    def test_normalize_file_uri_with_spaces_and_hash(self):
        result = normalize_file_input("file:///home/tamsy/Dokumen%20Baru/Slide%20%231.pptx")
        self.assertEqual(result, Path("/home/tamsy/Dokumen Baru/Slide #1.pptx"))

    def test_unique_output_path_avoids_existing_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "deck.pdf"
            base.touch()
            (Path(tmp) / "deck (1).pdf").touch()
            self.assertEqual(unique_output_path(base), Path(tmp) / "deck (2).pdf")

    def test_unique_dir_path_avoids_existing_pages_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages = Path(tmp) / "deck_pages"
            pages.mkdir()
            self.assertEqual(unique_dir_path(pages), Path(tmp) / "deck_pages (1)")

    def test_normalize_merged_filename_handles_blank_and_missing_ext(self):
        self.assertEqual(normalize_merged_filename("", "foto1"), "foto1_merged.pdf")
        self.assertEqual(normalize_merged_filename("laporan", "foto1"), "laporan.pdf")
        self.assertEqual(normalize_merged_filename("laporan.PDF", "foto1"), "laporan.PDF")

    def test_mixed_batch_same_dir_skips_matching_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.png"
            b = Path(tmp) / "b.jpg"
            a.touch()
            b.touch()
            jobs = plan_batch_actions([a, b], "jpg", out_dir=None)
            self.assertEqual([j.action for j in jobs], ["convert", "skip"])
            self.assertEqual(jobs[0].output_path, Path(tmp) / "a.jpg")

    def test_mixed_batch_different_out_dir_copies_matching_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            dst_dir = Path(tmp) / "dst"
            src_dir.mkdir()
            dst_dir.mkdir()
            a = src_dir / "a.png"
            b = src_dir / "b.jpg"
            a.touch()
            b.touch()
            jobs = plan_batch_actions([a, b], "jpg", out_dir=dst_dir)
            self.assertEqual([j.action for j in jobs], ["convert", "copy"])
            self.assertEqual(jobs[1].output_path, dst_dir / "b.jpg")

    def test_pdf_merge_creates_single_many_to_one_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.png"
            b = Path(tmp) / "b.jpg"
            a.touch()
            b.touch()
            jobs = plan_batch_actions([a, b], "pdf-merge", out_dir=None, merged_name="gabung")
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0].action, "merge_pdf")
            self.assertEqual(jobs[0].sources, (a, b))
            self.assertEqual(jobs[0].output_path, Path(tmp) / "gabung.pdf")

    def test_office_or_pdf_to_image_uses_pages_subdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            deck = Path(tmp) / "deck.pptx"
            deck.touch()
            jobs = plan_batch_actions([deck], "png", out_dir=None)
            self.assertTrue(jobs[0].is_multipage_dir)
            self.assertEqual(jobs[0].output_path, Path(tmp) / "deck_pages")


if __name__ == "__main__":
    unittest.main()
