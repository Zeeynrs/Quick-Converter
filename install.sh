#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "  Menginstal Quick Convert..."
echo "=========================================="

PREFIX_BIN="$HOME/.local/bin"
PREFIX_SHARE="$HOME/.local/share/quick-convert"
PREFIX_APP="$HOME/.local/share/applications"
PREFIX_KIO="$HOME/.local/share/kio/servicemenus"
PREFIX_K6="$HOME/.local/share/kservices6/ServiceMenus"
PREFIX_K5="$HOME/.local/share/kservices5/ServiceMenus"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$PREFIX_BIN" "$PREFIX_SHARE" "$PREFIX_APP" "$PREFIX_KIO" "$PREFIX_K6" "$PREFIX_K5"

echo "[1/4] Menyalin executable ke $PREFIX_BIN..."
cp "$SCRIPT_DIR/bin/quick-convert" "$PREFIX_BIN/quick-convert"
chmod +x "$PREFIX_BIN/quick-convert"

echo "[2/4] Menyalin modul Python ke $PREFIX_SHARE..."
rm -rf "$PREFIX_SHARE/quick_convert"
cp -r "$SCRIPT_DIR/src/quick_convert" "$PREFIX_SHARE/quick_convert"
rm -rf "$PREFIX_SHARE/quick_convert/__pycache__"

echo "[3/4] Mendaftarkan integrasi KDE Dolphin ServiceMenu..."
cp "$SCRIPT_DIR/desktop/quick-convert.desktop" "$PREFIX_APP/quick-convert.desktop"
cp "$SCRIPT_DIR/desktop/quick-convert-servicemenu.desktop" "$PREFIX_KIO/quick-convert.desktop"
ln -sf "$PREFIX_KIO/quick-convert.desktop" "$PREFIX_K6/quick-convert.desktop" 2>/dev/null || true
ln -sf "$PREFIX_KIO/quick-convert.desktop" "$PREFIX_K5/quick-convert.desktop" 2>/dev/null || true

echo "[4/4] Memperbarui cache desktop & KDE..."
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$PREFIX_APP" >/dev/null 2>&1 || true
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 --noincremental >/dev/null 2>&1 || true
fi

echo ""
echo "=========================================="
echo "  Quick Convert Berhasil Diinstal!"
echo "=========================================="
echo "Status engine konversi di sistem:"
for cmd in kdialog ffmpeg magick pdftoppm pdftotext pandoc; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "  [OK] $cmd"
    else
        echo "  [BELUM ADA] $cmd"
    fi
done
if command -v soffice >/dev/null 2>&1 || command -v libreoffice >/dev/null 2>&1; then
    echo "  [OK] libreoffice"
else
    echo "  [BELUM ADA] libreoffice (pasang dengan: sudo pacman -S libreoffice-fresh)"
fi
echo ""
echo "Jika Dolphin sedang terbuka, tutup dan buka kembali untuk memuat menu baru."
