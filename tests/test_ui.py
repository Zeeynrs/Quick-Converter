import sys
from pathlib import Path
import subprocess
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quick_convert.formats import TargetOption
from quick_convert.ui import (
    ProgressDialog,
    ask_merged_pdf_name,
    choose_output_directory,
    choose_target_format,
)


class TestUi(unittest.TestCase):
    def test_choose_target_format_uses_kdialog_menu_and_returns_selected_id(self):
        targets = [TargetOption("pdf", "PDF (.pdf)", ".pdf"), TargetOption("png", "PNG (.png)", ".png")]
        cmds = []

        def fake_run(cmd, **kwargs):
            cmds.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "pdf\n", "")

        selected = choose_target_format(targets, 1, run_fn=fake_run, which_fn=lambda n: "/usr/bin/kdialog")
        self.assertEqual(selected, "pdf")
        self.assertIn("--menu", cmds[0])

    def test_ask_merged_pdf_name_returns_none_on_cancel_and_default_on_blank(self):
        cancel_res = ask_merged_pdf_name(
            "foto1",
            run_fn=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", ""),
            which_fn=lambda n: "/usr/bin/kdialog",
        )
        blank_res = ask_merged_pdf_name(
            "foto1",
            run_fn=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "   \n", ""),
            which_fn=lambda n: "/usr/bin/kdialog",
        )
        custom_res = ask_merged_pdf_name(
            "foto1",
            run_fn=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "dokumen\n", ""),
            which_fn=lambda n: "/usr/bin/kdialog",
        )
        self.assertIsNone(cancel_res)
        self.assertEqual(blank_res, "foto1_merged.pdf")
        self.assertEqual(custom_res, "dokumen.pdf")

    def test_choose_output_directory_falls_back_to_zenity(self):
        cmds = []

        def fake_run(cmd, **kwargs):
            cmds.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "/tmp/out\n", "")

        selected = choose_output_directory(
            Path("/tmp"),
            run_fn=fake_run,
            which_fn=lambda n: "/usr/bin/zenity" if n == "zenity" else None,
        )
        self.assertEqual(selected, Path("/tmp/out"))
        self.assertEqual(cmds[0][0], "/usr/bin/zenity")

    def test_progress_dialog_ignores_qdbus_failures_gracefully(self):
        class FakeProc:
            def __init__(self):
                self.stdout = self

            def read(self):
                return "org.kde.kdialog-123 /ProgressDialog\n"

            def terminate(self):
                pass

        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            raise RuntimeError("no dbus")

        with ProgressDialog(
            "Konversi",
            2,
            popen_fn=lambda *a, **k: FakeProc(),
            run_fn=fake_run,
            which_fn=lambda n: f"/usr/bin/{n}",
        ) as dlg:
            dlg.advance(1, "Memproses 1/2")
        self.assertGreaterEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
