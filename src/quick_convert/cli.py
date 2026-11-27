"""CLI entrypoint dan orkestrator alur konversi quick-convert."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
from pathlib import Path
import sys

from quick_convert import __version__
from quick_convert.engines import find_missing_engines, run_conversion_job
from quick_convert.formats import get_valid_targets
from quick_convert.paths import normalize_file_input, plan_batch_actions
from quick_convert.ui import (
    ProgressDialog,
    ask_merged_pdf_name,
    choose_output_directory,
    choose_target_format,
    send_notification,
    show_error,
)

LOG_PATH = Path.home() / ".local" / "state" / "quick-convert" / "last.log"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quick-convert",
        description="Ubah format file dari menu klik kanan Dolphin atau terminal.",
    )
    parser.add_argument("files", nargs="*", help="Daftar file atau URI file:// yang akan dikonversi.")
    parser.add_argument("--choose-dir", action="store_true", help="Tanyakan folder tujuan setelah memilih format.")
    parser.add_argument("--to", dest="target_id", help="Format tujuan konversi (mode CLI non-interaktif).")
    parser.add_argument("--out-dir", dest="out_dir", help="Direktori output tujuan.")
    parser.add_argument("--merged-name", dest="merged_name", help="Nama file PDF gabungan (untuk pdf-merge).")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _write_error_log(failures: list[str]) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text("\n".join(failures) + "\n", encoding="utf-8")
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.files:
        show_error("Quick Convert", "Tidak ada file yang dipilih untuk dikonversi.")
        return 1

    files = [normalize_file_input(item) for item in args.files]
    for path in files:
        if path.is_dir():
            show_error("Quick Convert", f"Folder tidak didukung sebagai input konversi:\n{path}")
            return 1
        if not path.exists():
            show_error("Quick Convert", f"File tidak ditemukan:\n{path}")
            return 1

    valid_targets = get_valid_targets(files)
    if not valid_targets:
        show_error(
            "Quick Convert",
            "Format file tidak didukung atau kombinasi file terpilih tidak memiliki format tujuan yang sama.",
        )
        return 1

    interactive = args.target_id is None
    valid_ids = {opt.id for opt in valid_targets}

    if interactive:
        target_id = choose_target_format(valid_targets, len(files))
        if not target_id:
            return 0
    else:
        target_id = args.target_id.strip().lower()
        if target_id == "pdf" and "pdf" not in valid_ids and "pdf-each" in valid_ids:
            target_id = "pdf-each"
        if target_id not in valid_ids:
            allowed = ", ".join(opt.id for opt in valid_targets)
            show_error(
                "Quick Convert",
                f"Format tujuan '{target_id}' tidak valid untuk file terpilih.\nPilihan tersedia: {allowed}",
            )
            return 1

    merged_name = args.merged_name
    if target_id == "pdf-merge" and merged_name is None and interactive:
        merged_name = ask_merged_pdf_name(files[0].stem)
        if merged_name is None:
            return 0

    out_dir: Path | None = None
    if args.out_dir:
        out_dir = normalize_file_input(args.out_dir)
        if out_dir.exists() and not out_dir.is_dir():
            show_error("Quick Convert", f"Tujuan bukan direktori:\n{out_dir}")
            return 1
    elif args.choose_dir:
        out_dir = choose_output_directory(files[0].parent)
        if out_dir is None:
            return 0

    jobs = plan_batch_actions(files, target_id, out_dir, merged_name=merged_name)
    missing = find_missing_engines(jobs)
    if missing:
        lines = [f"- {m.name}: {m.install_hint}" for m in missing]
        show_error(
            "Engine Konversi Belum Terpasang",
            "Program berikut belum terpasang di sistem:\n\n" + "\n".join(lines),
        )
        return 1

    use_progress = interactive or len(jobs) > 1
    progress_ctx = ProgressDialog("Mengonversi file...", len(jobs)) if use_progress else nullcontext()

    ok_count = 0
    skip_count = 0
    fail_messages: list[str] = []
    last_out_dir = out_dir or files[0].parent

    with progress_ctx as dlg:
        for idx, job in enumerate(jobs, start=1):
            if dlg is not None:
                label = job.output_path.name if job.action == "merge_pdf" else job.sources[0].name
                dlg.advance(idx - 1, f"Memproses ({idx}/{len(jobs)}): {label}")
            res = run_conversion_job(job)
            if res.status == "ok":
                ok_count += 1
                last_out_dir = job.output_path.parent
            elif res.status == "skipped":
                skip_count += 1
            else:
                fail_messages.append(f"{job.sources[0].name}: {res.message}")
        if dlg is not None:
            dlg.advance(len(jobs), "Selesai")

    parts = [f"{ok_count} berhasil"]
    if skip_count:
        parts.append(f"{skip_count} dilewati")
    if fail_messages:
        parts.append(f"{len(fail_messages)} gagal")
    summary = f"{', '.join(parts)} ({last_out_dir})"

    if fail_messages:
        _write_error_log(fail_messages)
        send_notification("Quick Convert - Ada Kegagalan", summary, urgency="critical")
        show_error(
            "Sebagian Konversi Gagal",
            "\n".join(fail_messages[:5]) + f"\n\nLog lengkap: {LOG_PATH}",
        )
        return 1

    send_notification("Quick Convert Selesai", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
