import configparser
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class TestPackaging(unittest.TestCase):
    def test_servicemenu_desktop_contains_required_kde_keys_and_actions(self):
        path = ROOT / "desktop" / "quick-convert-servicemenu.desktop"
        self.assertTrue(path.exists())
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(path, encoding="utf-8")
        entry = cp["Desktop Entry"]
        self.assertEqual(entry["MimeType"], "all/allfiles;")
        self.assertEqual(entry["X-KDE-Priority"], "TopLevel")
        self.assertIn("convertHere", entry["Actions"])
        self.assertIn("convertTo", entry["Actions"])
        self.assertEqual(cp["Desktop Action convertHere"]["Exec"], "quick-convert %F")
        self.assertEqual(cp["Desktop Action convertTo"]["Exec"], "quick-convert --choose-dir %F")

    def test_cli_bin_help_and_real_image_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            img = Path(tmp) / "sample.png"
            subprocess.run(["magick", "-size", "16x16", "xc:blue", str(img)], check=True)
            res = subprocess.run(
                [str(ROOT / "bin" / "quick-convert"), "--to", "webp", str(img)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertTrue((Path(tmp) / "sample.webp").exists())


if __name__ == "__main__":
    unittest.main()
