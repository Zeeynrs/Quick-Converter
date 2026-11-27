import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quick_convert import cli


class TestCli(unittest.TestCase):
    def test_rejects_directory_input_with_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("quick_convert.cli.show_error") as mock_err:
                code = cli.main([tmp])
            self.assertEqual(code, 1)
            mock_err.assert_called_once()

    def test_cli_non_interactive_missing_engine_returns_nonzero_and_shows_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "slide.pptx"
            pptx.write_bytes(b"pptx")
            with patch("quick_convert.cli.find_missing_engines") as mock_missing, \
                 patch("quick_convert.cli.show_error") as mock_err:
                from quick_convert.engines import MissingEngine
                mock_missing.return_value = [MissingEngine("libreoffice", "sudo pacman -S libreoffice-fresh")]
                code = cli.main(["--to", "pdf", str(pptx)])
            self.assertEqual(code, 1)
            mock_err.assert_called_once()

    def test_interactive_cancel_on_format_picker_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            img = Path(tmp) / "a.png"
            img.write_bytes(b"png")
            with patch("quick_convert.cli.choose_target_format", return_value=None):
                code = cli.main([str(img)])
            self.assertEqual(code, 0)

    def test_cli_conversion_sends_summary_notification_and_logs_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            img = Path(tmp) / "a.png"
            img.write_bytes(b"png")
            log_file = Path(tmp) / "last.log"
            with patch("quick_convert.cli.LOG_PATH", log_file), \
                 patch("quick_convert.cli.find_missing_engines", return_value=[]), \
                 patch("quick_convert.cli.run_conversion_job") as mock_run, \
                 patch("quick_convert.cli.send_notification") as mock_notif, \
                 patch("quick_convert.cli.show_error") as mock_err:
                from quick_convert.engines import JobResult
                from quick_convert.paths import ConversionJob
                dummy_job = ConversionJob("convert", (img,), Path(tmp) / "a.jpg", "jpg", ".png")
                mock_run.return_value = JobResult(dummy_job, "error", "magick failed")
                code = cli.main(["--to", "jpg", str(img)])
            self.assertEqual(code, 1)
            mock_notif.assert_called_once()
            mock_err.assert_called_once()
            self.assertIn("magick failed", log_file.read_text())


if __name__ == "__main__":
    unittest.main()
