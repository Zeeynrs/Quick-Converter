"""Wrapper dialog native KDE (kdialog / qdbus6 / notify-send) dengan fallback zenity."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

from quick_convert.formats import TargetOption
from quick_convert.paths import normalize_file_input, normalize_merged_filename


def choose_target_format(
    targets: list[TargetOption],
    file_count: int,
    run_fn=subprocess.run,
    which_fn=shutil.which,
) -> str | None:
    """Membuka menu pilihan format tujuan menggunakan kdialog (atau zenity)."""
    if not targets:
        return None

    prompt = (
        f"Pilih format tujuan untuk {file_count} file:"
        if file_count > 1
        else "Pilih format tujuan konversi:"
    )

    kdialog = which_fn("kdialog")
    if kdialog:
        cmd = [kdialog, "--title", "Quick Convert", "--menu", prompt]
        for opt in targets:
            cmd.extend([opt.id, opt.label])
        proc = run_fn(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    zenity = which_fn("zenity")
    if zenity:
        cmd = [
            zenity,
            "--list",
            "--title=Quick Convert",
            f"--text={prompt}",
            "--column=ID",
            "--column=Format Tujuan",
            "--hide-column=1",
        ]
        for opt in targets:
            cmd.extend([opt.id, opt.label])
        proc = run_fn(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    return None


def choose_output_directory(
    initial_dir: Path,
    run_fn=subprocess.run,
    which_fn=shutil.which,
) -> Path | None:
    """Membuka dialog pemilih folder tujuan menggunakan kdialog atau zenity."""
    start_dir = str(initial_dir if initial_dir.is_dir() else Path.home())

    kdialog = which_fn("kdialog")
    if kdialog:
        proc = run_fn(
            [kdialog, "--title", "Quick Convert", "--getexistingdirectory", start_dir],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return normalize_file_input(proc.stdout.strip())
        return None

    zenity = which_fn("zenity")
    if zenity:
        proc = run_fn(
            [
                zenity,
                "--file-selection",
                "--directory",
                "--title=Pilih Folder Tujuan Konversi",
                f"--filename={start_dir}/",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return normalize_file_input(proc.stdout.strip())
        return None

    return None


def ask_merged_pdf_name(
    default_stem: str,
    run_fn=subprocess.run,
    which_fn=shutil.which,
) -> str | None:
    """Meminta nama file PDF gabungan dari pengguna; mengembalikan None bila dibatalkan."""
    default_name = f"{default_stem}_merged.pdf"

    kdialog = which_fn("kdialog")
    if kdialog:
        proc = run_fn(
            [
                kdialog,
                "--title",
                "Quick Convert",
                "--inputbox",
                "Nama file PDF gabungan:",
                default_name,
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return None
        return normalize_merged_filename(proc.stdout, default_stem)

    zenity = which_fn("zenity")
    if zenity:
        proc = run_fn(
            [
                zenity,
                "--entry",
                "--title=Quick Convert",
                "--text=Nama file PDF gabungan:",
                f"--entry-text={default_name}",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return None
        return normalize_merged_filename(proc.stdout, default_stem)

    return default_name


class ProgressDialog:
    """Context manager untuk progress bar kdialog melalui qdbus6/qdbus."""

    def __init__(
        self,
        title: str,
        total: int,
        popen_fn=subprocess.Popen,
        run_fn=subprocess.run,
        which_fn=shutil.which,
    ) -> None:
        self.title = title
        self.total = max(1, total)
        self._popen = popen_fn
        self._run = run_fn
        self._which = which_fn
        self._qdbus: str | None = which_fn("qdbus6") or which_fn("qdbus")
        self._service: str | None = None
        self._obj_path: str = "/ProgressDialog"
        self._proc = None

    def __enter__(self) -> ProgressDialog:
        kdialog = self._which("kdialog")
        if not kdialog or not self._qdbus:
            return self
        try:
            self._proc = self._popen(
                [kdialog, "--title", "Quick Convert", "--progressbar", self.title, str(self.total)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if self._proc and self._proc.stdout:
                ref = self._proc.stdout.read().strip()
                parts = ref.split()
                if parts:
                    self._service = parts[0]
                    if len(parts) > 1:
                        self._obj_path = parts[1]
        except Exception:
            self._service = None
        return self

    def advance(self, step: int, label: str) -> None:
        if not self._service or not self._qdbus:
            return
        try:
            self._run(
                [self._qdbus, self._service, self._obj_path, "Set", "", "value", str(step)],
                capture_output=True,
                text=True,
                timeout=3,
            )
            self._run(
                [self._qdbus, self._service, self._obj_path, "setLabelText", label],
                capture_output=True,
                text=True,
                timeout=3,
            )
        except Exception:
            pass

    def close(self) -> None:
        if self._service and self._qdbus:
            try:
                self._run(
                    [self._qdbus, self._service, self._obj_path, "close"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
            except Exception:
                pass
        if self._proc is not None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        self._service = None

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def show_error(
    title: str,
    message: str,
    run_fn=subprocess.run,
    which_fn=shutil.which,
) -> None:
    """Menampilkan pesan error lewat kdialog, zenity, atau notify-send + stderr."""
    print(f"[{title}] {message}", file=sys.stderr)
    kdialog = which_fn("kdialog")
    if kdialog:
        try:
            run_fn([kdialog, "--title", title, "--error", message], check=False)
            return
        except Exception:
            pass
    zenity = which_fn("zenity")
    if zenity:
        try:
            run_fn([zenity, "--error", f"--title={title}", f"--text={message}"], check=False)
            return
        except Exception:
            pass
    send_notification(title, message, urgency="critical", run_fn=run_fn, which_fn=which_fn)


def send_notification(
    title: str,
    message: str,
    urgency: str = "normal",
    run_fn=subprocess.run,
    which_fn=shutil.which,
) -> None:
    """Mengirim notifikasi desktop melalui notify-send jika tersedia."""
    notify = which_fn("notify-send")
    if not notify:
        return
    try:
        run_fn(
            [notify, "-a", "Quick Convert", "-i", "view-refresh", "-u", urgency, title, message],
            timeout=5,
            check=False,
        )
    except Exception:
        pass
