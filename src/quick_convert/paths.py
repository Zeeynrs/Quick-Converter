"""Normalisasi path input, penamaan output unik, dan perencana aksi batch."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import urllib.parse

from quick_convert.formats import TARGET_CATALOG, get_file_category


@dataclass(frozen=True)
class ConversionJob:
    """Satu unit pekerjaan konversi, salin, skip, atau penggabungan PDF."""

    action: str  # "convert" | "copy" | "skip" | "merge_pdf"
    sources: tuple[Path, ...]
    output_path: Path
    target_id: str
    src_ext: str
    is_multipage_dir: bool = False


def normalize_file_input(raw: str) -> Path:
    """Mengubah URI file:// atau path relatif menjadi Path absolut."""
    text = raw.strip()
    if text.startswith("file://"):
        parsed = urllib.parse.urlsplit(text)
        raw_path = parsed.path
        if parsed.fragment:
            raw_path = f"{raw_path}#{parsed.fragment}"
        decoded = urllib.parse.unquote(raw_path)
    else:
        decoded = os.path.expanduser(text)
    return Path(os.path.abspath(decoded))


def normalize_merged_filename(raw: str, default_stem: str) -> str:
    """Menormalisasi nama file PDF gabungan dari input user atau CLI."""
    cleaned = Path(raw.strip()).name if raw.strip() else ""
    if not cleaned:
        return f"{default_stem}_merged.pdf"
    if not cleaned.lower().endswith(".pdf"):
        return f"{cleaned}.pdf"
    return cleaned


def _reserve_unique_path(candidate: Path, reserved: set[Path], is_dir: bool = False) -> Path:
    """Mencari path unik yang belum ada di disk maupun di set reserved."""
    def taken(p: Path) -> bool:
        return p in reserved or p.exists()

    if not taken(candidate):
        reserved.add(candidate)
        return candidate

    parent = candidate.parent
    if is_dir:
        base = candidate.name
        idx = 1
        while True:
            attempt = parent / f"{base} ({idx})"
            if not taken(attempt):
                reserved.add(attempt)
                return attempt
            idx += 1

    stem = candidate.stem
    suffix = candidate.suffix
    idx = 1
    while True:
        attempt = parent / f"{stem} ({idx}){suffix}"
        if not taken(attempt):
            reserved.add(attempt)
            return attempt
        idx += 1


def unique_output_path(path: Path) -> Path:
    """Mengembalikan path file unik tanpa menimpa file yang sudah ada."""
    return _reserve_unique_path(path, set(), is_dir=False)


def unique_dir_path(path: Path) -> Path:
    """Mengembalikan path direktori unik tanpa menimpa direktori yang sudah ada."""
    return _reserve_unique_path(path, set(), is_dir=True)


def plan_batch_actions(
    files: list[Path],
    target_id: str,
    out_dir: Path | None,
    merged_name: str | None = None,
) -> list[ConversionJob]:
    """Merencanakan daftar ConversionJob untuk file tunggal maupun batch."""
    if not files:
        return []

    target = TARGET_CATALOG[target_id]
    reserved: set[Path] = set()

    if target.is_merge:
        dest_dir = out_dir if out_dir is not None else files[0].parent
        filename = normalize_merged_filename(merged_name or "", files[0].stem)
        out_path = _reserve_unique_path(dest_dir / filename, reserved, is_dir=False)
        return [
            ConversionJob(
                action="merge_pdf",
                sources=tuple(files),
                output_path=out_path,
                target_id=target_id,
                src_ext=files[0].suffix.lower(),
                is_multipage_dir=False,
            )
        ]

    jobs: list[ConversionJob] = []
    dst_ext = target.output_ext.lower()

    for src in files:
        src_ext = src.suffix.lower()
        cat = get_file_category(src)
        dest_dir = out_dir if out_dir is not None else src.parent
        same_dir = dest_dir.resolve() == src.parent.resolve()

        if src_ext == dst_ext:
            if same_dir:
                jobs.append(
                    ConversionJob(
                        action="skip",
                        sources=(src,),
                        output_path=src,
                        target_id=target_id,
                        src_ext=src_ext,
                    )
                )
            else:
                out_path = _reserve_unique_path(dest_dir / src.name, reserved, is_dir=False)
                jobs.append(
                    ConversionJob(
                        action="copy",
                        sources=(src,),
                        output_path=out_path,
                        target_id=target_id,
                        src_ext=src_ext,
                    )
                )
            continue

        is_multipage = cat in ("office", "pdf") and target_id in ("png", "jpg", "webp")
        if is_multipage:
            out_path = _reserve_unique_path(dest_dir / f"{src.stem}_pages", reserved, is_dir=True)
        else:
            out_path = _reserve_unique_path(dest_dir / f"{src.stem}{dst_ext}", reserved, is_dir=False)

        jobs.append(
            ConversionJob(
                action="convert",
                sources=(src,),
                output_path=out_path,
                target_id=target_id,
                src_ext=src_ext,
                is_multipage_dir=is_multipage,
            )
        )

    return jobs
