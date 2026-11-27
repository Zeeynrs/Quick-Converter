"""Katalog ekstensi file, format tujuan konversi, dan pemetaan engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TargetOption:
    """Satu pilihan format tujuan pada menu konversi."""

    id: str
    label: str
    output_ext: str
    is_merge: bool = False


TARGET_CATALOG: dict[str, TargetOption] = {
    "pdf": TargetOption("pdf", "PDF (.pdf)", ".pdf"),
    "pdf-each": TargetOption("pdf-each", "PDF — 1 file per gambar (.pdf)", ".pdf", is_merge=False),
    "pdf-merge": TargetOption("pdf-merge", "PDF — Gabung jadi 1 PDF (.pdf)", ".pdf", is_merge=True),
    "pptx": TargetOption("pptx", "PowerPoint (.pptx)", ".pptx"),
    "odp": TargetOption("odp", "OpenDocument Presentation (.odp)", ".odp"),
    "docx": TargetOption("docx", "Word (.docx)", ".docx"),
    "odt": TargetOption("odt", "OpenDocument Text (.odt)", ".odt"),
    "rtf": TargetOption("rtf", "Rich Text (.rtf)", ".rtf"),
    "xlsx": TargetOption("xlsx", "Excel (.xlsx)", ".xlsx"),
    "ods": TargetOption("ods", "OpenDocument Spreadsheet (.ods)", ".ods"),
    "csv": TargetOption("csv", "CSV (.csv)", ".csv"),
    "html": TargetOption("html", "HTML (.html)", ".html"),
    "txt": TargetOption("txt", "Teks Polos (.txt)", ".txt"),
    "epub": TargetOption("epub", "EPUB (.epub)", ".epub"),
    "png": TargetOption("png", "PNG (.png)", ".png"),
    "jpg": TargetOption("jpg", "JPEG (.jpg)", ".jpg"),
    "webp": TargetOption("webp", "WebP (.webp)", ".webp"),
    "bmp": TargetOption("bmp", "BMP (.bmp)", ".bmp"),
    "tiff": TargetOption("tiff", "TIFF (.tiff)", ".tiff"),
    "gif": TargetOption("gif", "GIF (.gif)", ".gif"),
    "ico": TargetOption("ico", "Icon (.ico)", ".ico"),
    "mp4": TargetOption("mp4", "MP4 (.mp4)", ".mp4"),
    "mkv": TargetOption("mkv", "MKV (.mkv)", ".mkv"),
    "webm": TargetOption("webm", "WebM (.webm)", ".webm"),
    "mov": TargetOption("mov", "MOV (.mov)", ".mov"),
    "avi": TargetOption("avi", "AVI (.avi)", ".avi"),
    "mp3": TargetOption("mp3", "MP3 (.mp3)", ".mp3"),
    "wav": TargetOption("wav", "WAV (.wav)", ".wav"),
    "flac": TargetOption("flac", "FLAC (.flac)", ".flac"),
    "ogg": TargetOption("ogg", "OGG Vorbis (.ogg)", ".ogg"),
    "m4a": TargetOption("m4a", "M4A (.m4a)", ".m4a"),
    "aac": TargetOption("aac", "AAC (.aac)", ".aac"),
}

EXTENSION_CATEGORY: dict[str, str] = {
    ".pptx": "office",
    ".ppt": "office",
    ".odp": "office",
    ".docx": "office",
    ".doc": "office",
    ".odt": "office",
    ".rtf": "office",
    ".xlsx": "office",
    ".xls": "office",
    ".ods": "office",
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".tif": "image",
    ".gif": "image",
    ".svg": "image",
    ".ico": "image",
    ".heic": "image",
    ".mp4": "video",
    ".mkv": "video",
    ".webm": "video",
    ".mov": "video",
    ".avi": "video",
    ".mp3": "audio",
    ".wav": "audio",
    ".flac": "audio",
    ".ogg": "audio",
    ".m4a": "audio",
    ".aac": "audio",
    ".md": "markup",
    ".markdown": "markup",
    ".html": "markup",
    ".htm": "markup",
    ".txt": "markup",
    ".rst": "markup",
}

_OFFICE_PRESENTATION = (".pptx", ".ppt", ".odp")
_OFFICE_DOCUMENT = (".docx", ".doc", ".odt", ".rtf")
_OFFICE_SPREADSHEET = (".xlsx", ".xls", ".ods")

_TARGETS_BY_GROUP: dict[str, tuple[str, ...]] = {
    "office_pres": ("pdf", "pptx", "odp", "png", "jpg", "webp"),
    "office_doc": ("pdf", "docx", "odt", "rtf", "txt", "html", "png", "jpg", "webp"),
    "office_sheet": ("pdf", "xlsx", "ods", "csv", "png", "jpg", "webp"),
    "pdf": ("png", "jpg", "webp", "txt"),
    "image": ("png", "jpg", "webp", "bmp", "tiff", "gif", "ico", "pdf"),
    "video": ("mp4", "mkv", "webm", "mov", "avi", "gif", "mp3", "wav", "flac", "m4a", "ogg", "aac"),
    "audio": ("mp3", "wav", "flac", "ogg", "m4a", "aac"),
    "markup": ("pdf", "docx", "html", "txt", "epub"),
}

_EXT_ALIAS: dict[str, str] = {
    ".jpeg": "jpg",
    ".tif": "tiff",
    ".htm": "html",
    ".markdown": "md",
}


def get_file_category(path: str | Path) -> str | None:
    """Mengembalikan kategori file berdasarkan ekstensi, atau None jika tidak didukung."""
    ext = Path(path).suffix.lower()
    return EXTENSION_CATEGORY.get(ext)


def _group_for_ext(ext: str) -> str | None:
    if ext in _OFFICE_PRESENTATION:
        return "office_pres"
    if ext in _OFFICE_DOCUMENT:
        return "office_doc"
    if ext in _OFFICE_SPREADSHEET:
        return "office_sheet"
    return EXTENSION_CATEGORY.get(ext)


def _canonical_target_for_ext(ext: str) -> str:
    return _EXT_ALIAS.get(ext, ext.lstrip("."))


def get_valid_targets(files: list[str] | list[Path]) -> list[TargetOption]:
    """Menentukan daftar TargetOption yang valid untuk satu atau sekumpulan file."""
    if not files:
        return []

    per_file_orders: list[tuple[str, ...]] = []
    exts: list[str] = []
    categories: list[str] = []

    for item in files:
        ext = Path(item).suffix.lower()
        group = _group_for_ext(ext)
        cat = EXTENSION_CATEGORY.get(ext)
        if not group or not cat:
            return []
        exts.append(ext)
        categories.append(cat)
        per_file_orders.append(_TARGETS_BY_GROUP[group])

    common_ids: list[str] = [
        tid
        for tid in per_file_orders[0]
        if all(tid in order for order in per_file_orders[1:])
    ]

    if len(files) == 1:
        own_id = _canonical_target_for_ext(exts[0])
        common_ids = [tid for tid in common_ids if tid != own_id]
        return [TARGET_CATALOG[tid] for tid in common_ids]

    # Untuk 2+ gambar, pecah opsi "pdf" menjadi dua mode: per-file dan gabung.
    all_images = all(cat == "image" for cat in categories)
    expanded: list[str] = []
    for tid in common_ids:
        if tid == "pdf" and all_images:
            expanded.extend(["pdf-each", "pdf-merge"])
        else:
            expanded.append(tid)

    return [TARGET_CATALOG[tid] for tid in expanded]


def required_engines(src_ext: str, target_id: str) -> tuple[str, ...]:
    """Mengembalikan tuple nama engine yang diperlukan untuk pasangan ekstensi asal dan target."""
    ext = src_ext.lower()
    cat = EXTENSION_CATEGORY.get(ext)
    if not cat:
        return ()

    if cat == "office":
        if target_id in ("png", "jpg", "webp"):
            return ("libreoffice", "pdftoppm")
        return ("libreoffice",)

    if cat == "pdf":
        if target_id == "txt":
            return ("pdftotext",)
        return ("pdftoppm",)

    if cat == "image":
        return ("magick",)

    if cat in ("video", "audio"):
        return ("ffmpeg",)

    if cat == "markup":
        return ("pandoc",)

    return ()
