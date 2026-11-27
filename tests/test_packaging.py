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

    def test_bin_prefers_repo_src_over_installed_package(self):
        with tempfile.TemporaryDirectory() as fake_home:
            shadow = Path(fake_home) / ".local" / "share" / "quick-convert" / "quick_convert"
            shadow.mkdir(parents=True)
            (shadow / "__init__.py").write_text('__version__ = "99.99.99-stale"\n', encoding="utf-8")
            (shadow / "cli.py").write_text('def main():\n    print("STALE")\n    return 0\n', encoding="utf-8")
            env = {"HOME": fake_home, "PATH": "/usr/bin:/bin"}
            res = subprocess.run(
                [str(ROOT / "bin" / "quick-convert"), "--version"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertNotIn("STALE", res.stdout)
            self.assertIn("1.0.0", res.stdout)


if __name__ == "__main__":
    unittest.main()
