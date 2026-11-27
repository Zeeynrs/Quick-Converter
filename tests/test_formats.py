import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quick_convert.formats import (
    get_file_category,
    get_valid_targets,
    required_engines,
)


class TestFormats(unittest.TestCase):
    def test_single_pptx_offers_pdf_and_images_not_pptx(self):
        targets = [t.id for t in get_valid_targets(["/tmp/slide.pptx"])]
        self.assertIn("pdf", targets)
        self.assertIn("png", targets)
        self.assertNotIn("pptx", targets)

    def test_single_png_excludes_own_format_and_pdf_merge(self):
        targets = [t.id for t in get_valid_targets(["/tmp/foto.png"])]
        self.assertIn("jpg", targets)
        self.assertIn("pdf", targets)
        self.assertNotIn("png", targets)
        self.assertNotIn("pdf-merge", targets)
        self.assertNotIn("pdf-each", targets)

    def test_multi_images_mixed_include_common_formats_and_both_pdf_modes(self):
        targets = [t.id for t in get_valid_targets(["/tmp/a.png", "/tmp/b.jpg"])]
        self.assertIn("png", targets)
        self.assertIn("jpg", targets)
        self.assertIn("webp", targets)
        self.assertIn("pdf-each", targets)
        self.assertIn("pdf-merge", targets)
        self.assertNotIn("pdf", targets)

    def test_mixed_office_batch_intersects_on_pdf_and_images(self):
        targets = [t.id for t in get_valid_targets(["/tmp/a.pptx", "/tmp/b.docx"])]
        self.assertIn("pdf", targets)
        self.assertIn("png", targets)

    def test_incompatible_batch_returns_empty_targets(self):
        targets = get_valid_targets(["/tmp/a.mp3", "/tmp/b.pptx"])
        self.assertEqual(targets, [])

    def test_required_engines_for_office_to_png_needs_libreoffice_and_pdftoppm(self):
        self.assertEqual(required_engines(".pptx", "png"), ("libreoffice", "pdftoppm"))
        self.assertEqual(required_engines(".pptx", "pdf"), ("libreoffice",))
        self.assertEqual(required_engines(".md", "pdf"), ("pandoc",))
        self.assertEqual(required_engines(".mp4", "mp3"), ("ffmpeg",))
        self.assertEqual(required_engines(".png", "pdf-merge"), ("magick",))


if __name__ == "__main__":
    unittest.main()
