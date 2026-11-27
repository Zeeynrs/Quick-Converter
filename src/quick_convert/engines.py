"""Deteksi ketersediaan engine eksternal dan eksekutor konversi file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile

from quick_convert.formats import get_file_category, required_engines
from quick_convert.paths import ConversionJob

_INSTALL_HINTS: dict[str, str] = {
    "libreoffice": "sudo pacman -S libreoffice-fresh  # atau libreoffice-still",
    "pandoc": "sudo pacman -S pandoc",
    "ffmpeg": "sudo pacman -S ffmpeg",
    "magick": "sudo pacman -S imagemagick",
    "pdftoppm": "sudo pacman -S poppler",
    "pdftotext": "sudo pacman -S poppler",
}


@dataclass(frozen=True)
class MissingEngine:
    """Informasi engine yang belum terpasang beserta saran instalasi."""

    name: str
    install_hint: str


@dataclass(frozen=True)
class JobResult:
    """Hasil eksekusi satu ConversionJob."""

    job: ConversionJob
    status: str  # "ok" | "skipped" | "error"
    message: str


def _resolve_engine_binary(name: str, which_fn=shutil.which) -> str | None:
    if name == "libreoffice":
        return which_fn("soffice") or which_fn("libreoffice")
    return which_fn(name)


def find_missing_engines(jobs: list[ConversionJob], which_fn=shutil.which) -> list[MissingEngine]:
    """Memeriksa apakah seluruh engine yang dibutuhkan daftar job tersedia di PATH."""
    seen: set[str] = set()
    missing: list[MissingEngine] = []

    for job in jobs:
        if job.action in ("skip", "copy"):
            continue
        needed = list(required_engines(job.src_ext, job.target_id))
        if job.target_id == "webp" and get_file_category(job.sources[0]) in ("office", "pdf"):
            needed.append("magick")
        for eng in needed:
            if eng in seen:
                continue
            seen.add(eng)
            if not _resolve_engine_binary(eng, which_fn=which_fn):
                missing.append(MissingEngine(eng, _INSTALL_HINTS.get(eng, eng)))

    return missing


def build_libreoffice_cmd(
    binary: str,
    user_profile_dir: Path,
    out_dir: Path,
    target_ext: str,
    source: Path,
) -> list[str]:
    """Membangun argumen LibreOffice headless dengan profil sementara yang terisolasi."""
    return [
        binary,
        "--headless",
        "--norestore",
        f"-env:UserInstallation=file://{user_profile_dir}",
        "--convert-to",
        target_ext,
        "--outdir",
        str(out_dir),
        str(source),
    ]


def _run_checked(cmd: list[str], run_fn) -> tuple[bool, str]:
    proc = run_fn(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return True, ""
    err = (proc.stderr or proc.stdout or f"Kode keluar {proc.returncode}").strip()
    return False, err


def _render_pdf_to_images(
    pdf_path: Path,
    pages_dir: Path,
    stem: str,
    target_id: str,
    run_fn,
    which_fn,
) -> tuple[bool, str]:
    pdftoppm = _resolve_engine_binary("pdftoppm", which_fn=which_fn)
    if not pdftoppm:
        return False, "Engine pdftoppm tidak ditemukan"

    pages_dir.mkdir(parents=True, exist_ok=True)
    if target_id == "webp":
        magick = _resolve_engine_binary("magick", which_fn=which_fn)
        if not magick:
            return False, "Engine magick tidak ditemukan"
        with tempfile.TemporaryDirectory() as tmp_img_dir:
            prefix = Path(tmp_img_dir) / stem
            ok, err = _run_checked([pdftoppm, "-r", "150", "-png", str(pdf_path), str(prefix)], run_fn)
            if not ok:
                return False, err
            for png_file in sorted(Path(tmp_img_dir).glob("*.png")):
                out_webp = pages_dir / f"{png_file.stem}.webp"
                ok, err = _run_checked([magick, str(png_file), str(out_webp)], run_fn)
                if not ok:
                    return False, err
        return True, f"Halaman disimpan ke {pages_dir}"

    fmt_flag = "-jpeg" if target_id == "jpg" else "-png"
    prefix = pages_dir / stem
    ok, err = _run_checked([pdftoppm, "-r", "150", fmt_flag, str(pdf_path), str(prefix)], run_fn)
    if not ok:
        return False, err
    return True, f"Halaman disimpan ke {pages_dir}"


def _run_libreoffice_single(
    src: Path,
    out_dir: Path,
    target_ext: str,
    run_fn,
    which_fn,
) -> tuple[bool, Path | str]:
    lo = _resolve_engine_binary("libreoffice", which_fn=which_fn)
    if not lo:
        return False, "Engine libreoffice tidak ditemukan"

    with tempfile.TemporaryDirectory() as profile_dir:
        cmd = build_libreoffice_cmd(lo, Path(profile_dir), out_dir, target_ext, src)
        ok, err = _run_checked(cmd, run_fn)
        if not ok:
            return False, err

    expected = out_dir / f"{src.stem}.{target_ext}"
    if expected.exists():
        return True, expected
    generated = sorted(out_dir.glob(f"*.{target_ext}"))
    if generated:
        return True, generated[0]
    return False, f"LibreOffice tidak menghasilkan file .{target_ext}"


def run_conversion_job(
    job: ConversionJob,
    run_fn=subprocess.run,
    which_fn=shutil.which,
) -> JobResult:
    """Menjalankan satu ConversionJob dan mengembalikan JobResult."""
    if job.action == "skip":
        return JobResult(job, "skipped", f"Dilewati (sudah .{job.target_id}): {job.sources[0].name}")

    try:
        if job.action == "copy":
            job.output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(job.sources[0], job.output_path)
            return JobResult(job, "ok", f"Disalin ke {job.output_path}")

        if job.action == "merge_pdf":
            magick = _resolve_engine_binary("magick", which_fn=which_fn)
            if not magick:
                return JobResult(job, "error", "Engine magick tidak ditemukan")
            job.output_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = [magick, *[str(s) for s in job.sources], str(job.output_path)]
            ok, err = _run_checked(cmd, run_fn)
            return JobResult(job, "ok" if ok else "error", f"Digabung ke {job.output_path}" if ok else err)

        src = job.sources[0]
        cat = get_file_category(src)
        job.output_path.parent.mkdir(parents=True, exist_ok=True)

        if cat == "office":
            if job.is_multipage_dir:
                with tempfile.TemporaryDirectory() as tmp_pdf_dir:
                    ok, pdf_or_err = _run_libreoffice_single(src, Path(tmp_pdf_dir), "pdf", run_fn, which_fn)
                    if not ok:
                        return JobResult(job, "error", str(pdf_or_err))
                    ok_img, msg_img = _render_pdf_to_images(
                        Path(pdf_or_err),
                        job.output_path,
                        src.stem,
                        job.target_id,
                        run_fn,
                        which_fn,
                    )
                    return JobResult(job, "ok" if ok_img else "error", msg_img)

            with tempfile.TemporaryDirectory() as tmp_out_dir:
                ok, out_or_err = _run_libreoffice_single(src, Path(tmp_out_dir), job.target_id, run_fn, which_fn)
                if not ok:
                    return JobResult(job, "error", str(out_or_err))
                shutil.move(str(out_or_err), str(job.output_path))
                return JobResult(job, "ok", f"Berhasil diubah ke {job.output_path}")

        if cat == "pdf":
            if job.target_id == "txt":
                pdftotext = _resolve_engine_binary("pdftotext", which_fn=which_fn)
                if not pdftotext:
                    return JobResult(job, "error", "Engine pdftotext tidak ditemukan")
                ok, err = _run_checked([pdftotext, str(src), str(job.output_path)], run_fn)
                return JobResult(job, "ok" if ok else "error", f"Berhasil diubah ke {job.output_path}" if ok else err)

            ok, msg = _render_pdf_to_images(src, job.output_path, src.stem, job.target_id, run_fn, which_fn)
            return JobResult(job, "ok" if ok else "error", msg)

        if cat == "image":
            magick = _resolve_engine_binary("magick", which_fn=which_fn)
            if not magick:
                return JobResult(job, "error", "Engine magick tidak ditemukan")
            ok, err = _run_checked([magick, str(src), str(job.output_path)], run_fn)
            return JobResult(job, "ok" if ok else "error", f"Berhasil diubah ke {job.output_path}" if ok else err)

        if cat in ("video", "audio"):
            ffmpeg = _resolve_engine_binary("ffmpeg", which_fn=which_fn)
            if not ffmpeg:
                return JobResult(job, "error", "Engine ffmpeg tidak ditemukan")
            cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src)]
            if job.target_id == "gif":
                cmd.extend(["-vf", "fps=12,scale=720:-1:flags=lanczos"])
            elif job.target_id in ("mp3", "wav", "flac", "ogg", "m4a", "aac"):
                cmd.append("-vn")
            cmd.append(str(job.output_path))
            ok, err = _run_checked(cmd, run_fn)
            return JobResult(job, "ok" if ok else "error", f"Berhasil diubah ke {job.output_path}" if ok else err)

        if cat == "markup":
            pandoc = _resolve_engine_binary("pandoc", which_fn=which_fn)
            if not pandoc:
                return JobResult(job, "error", "Engine pandoc tidak ditemukan")
            ok, err = _run_checked([pandoc, str(src), "-o", str(job.output_path)], run_fn)
            return JobResult(job, "ok" if ok else "error", f"Berhasil diubah ke {job.output_path}" if ok else err)

        return JobResult(job, "error", f"Kategori tidak didukung: {src.suffix}")

    except Exception as exc:
        return JobResult(job, "error", str(exc))
