import sys
import tempfile
from pathlib import Path
import subprocess
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quick_convert.engines import (
    build_libreoffice_cmd,
    find_missing_engines,
    run_conversion_job,
)
from quick_convert.paths import ConversionJob


class TestEngines(unittest.TestCase):
    def test_find_missing_engines_reports_libreoffice_pacman_hint(self):
        job = ConversionJob("convert", (Path("/tmp/a.pptx"),), Path("/tmp/a.pdf"), "pdf", ".pptx")
        missing = find_missing_engines([job], which_fn=lambda _: None)
        names = [m.name for m in missing]
        self.assertIn("libreoffice", names)
        self.assertIn("sudo pacman -S libreoffice-fresh", missing[0].install_hint)

    def test_build_libreoffice_cmd_uses_isolated_user_installation(self):
        cmd = build_libreoffice_cmd(
            "/usr/bin/soffice",
            Path("/tmp/lo-profile"),
            Path("/tmp/out"),
            "pdf",
            Path("/tmp/slide.pptx"),
        )
        self.assertIn("--headless", cmd)
        self.assertIn("-env:UserInstallation=file:///tmp/lo-profile", cmd)
        self.assertIn("--convert-to", cmd)

    def test_run_conversion_job_skip_and_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "a.jpg"
            src.write_bytes(b"imgdata")
            dst = Path(tmp) / "out.jpg"
            skip_job = ConversionJob("skip", (src,), src, "jpg", ".jpg")
            copy_job = ConversionJob("copy", (src,), dst, "jpg", ".jpg")

            res_skip = run_conversion_job(skip_job)
            res_copy = run_conversion_job(copy_job)

            self.assertEqual(res_skip.status, "skipped")
            self.assertEqual(res_copy.status, "ok")
            self.assertEqual(dst.read_bytes(), b"imgdata")

    def test_run_conversion_job_office_to_png_two_stage_and_moves_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "deck.pptx"
            src.write_bytes(b"pptx")
            pages_dir = Path(tmp) / "deck_pages"
            calls = []

            def fake_run(cmd, **kwargs):
                calls.append(cmd)
                if "--convert-to" in cmd:
                    out_idx = cmd.index("--outdir") + 1
                    (Path(cmd[out_idx]) / "deck.pdf").write_bytes(b"%PDF")
                elif "pdftoppm" in cmd[0]:
                    prefix = Path(cmd[-1])
                    Path(f"{prefix}-1.png").write_bytes(b"png1")
                return subprocess.CompletedProcess(cmd, 0, "", "")

            job = ConversionJob("convert", (src,), pages_dir, "png", ".pptx", is_multipage_dir=True)
            res = run_conversion_job(job, run_fn=fake_run, which_fn=lambda n: f"/usr/bin/{n}")
            self.assertEqual(res.status, "ok")
            self.assertTrue((pages_dir / "deck-1.png").exists())
            self.assertEqual(len(calls), 2)

    def test_run_conversion_job_merge_pdf_invokes_magick_with_all_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "1.png"
            b = Path(tmp) / "2.jpg"
            a.touch()
            b.touch()
            out_pdf = Path(tmp) / "merged.pdf"
            recorded = []

            def fake_run(cmd, **kwargs):
                recorded.append(cmd)
                out_pdf.write_bytes(b"%PDF")
                return subprocess.CompletedProcess(cmd, 0, "", "")

            job = ConversionJob("merge_pdf", (a, b), out_pdf, "pdf-merge", ".png")
            res = run_conversion_job(job, run_fn=fake_run, which_fn=lambda n: f"/usr/bin/{n}")
            self.assertEqual(res.status, "ok")
            self.assertEqual(recorded[0], ["/usr/bin/magick", str(a), str(b), str(out_pdf)])


if __name__ == "__main__":
    unittest.main()
