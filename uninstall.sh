#!/usr/bin/env bash
set -euo pipefail

echo "Menghapus instalasi Quick Convert..."

rm -f "$HOME/.local/bin/quick-convert"
rm -rf "$HOME/.local/share/quick-convert"
rm -f "$HOME/.local/share/applications/quick-convert.desktop"
rm -f "$HOME/.local/share/kio/servicemenus/quick-convert.desktop"
rm -f "$HOME/.local/share/kservices6/ServiceMenus/quick-convert.desktop"
rm -f "$HOME/.local/share/kservices5/ServiceMenus/quick-convert.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 --noincremental >/dev/null 2>&1 || true
fi

echo "Quick Convert berhasil dihapus."
