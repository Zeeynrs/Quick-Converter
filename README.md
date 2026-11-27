# Quick Convert

Utilitas konversi file serbaguna dengan integrasi menu klik kanan **KDE Dolphin** menggunakan dialog native `kdialog`.

## Fitur

- **Menu Klik Kanan Dolphin (`Ubah Format`):**
  - **Ubah Format di Sini...**: Memilih format tujuan dan menyimpan hasil di folder file asal.
  - **Ubah Format ke Folder...**: Memilih format tujuan lalu memilih folder penyimpanan.
- **Format yang Didukung:**
  - **Dokumen Office:** `.pptx`, `.ppt`, `.odp`, `.docx`, `.doc`, `.odt`, `.rtf`, `.xlsx`, `.xls`, `.ods` -> `.pdf`, antar format Office, atau gambar halaman (`<nama>_pages/`).
  - **PDF:** `.pdf` -> gambar halaman (`.png`, `.jpg`, `.webp`) atau `.txt`.
  - **Gambar:** `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`, `.gif`, `.svg`, `.ico`, `.heic` -> antar format gambar atau `.pdf` (per gambar maupun gabung jadi 1 PDF).
  - **Audio & Video:** `.mp4`, `.mkv`, `.webm`, `.mov`, `.avi`, `.mp3`, `.wav`, `.flac`, `.ogg`, `.m4a`, `.aac` -> antar format media, ekstraksi audio, atau `.gif`.
  - **Markup/Teks:** `.md`, `.html`, `.txt`, `.rst` -> `.pdf`, `.docx`, `.html`, `.txt`, `.epub`.
- **Aman untuk Batch:** Tidak menimpa file yang sudah ada (menambahkan akhiran `(1)`, `(2)`, dst.) dan mendukung seleksi campuran banyak file.

## Dependensi

- **UI & Notifikasi:** `kdialog`, `qdbus6`/`qdbus`, `notify-send`
- **Gambar & PDF:** `imagemagick` (`magick`), `poppler` (`pdftoppm`, `pdftotext`)
- **Audio & Video:** `ffmpeg`
- **Dokumen Office (opsional/disarankan untuk `.pptx`/`.docx`):** `libreoffice-fresh` atau `libreoffice-still`
- **Markup (opsional):** `pandoc`

## Instalasi

```bash
./install.sh
```

Untuk menghapus instalasi:

```bash
./uninstall.sh
```

## Contoh Penggunaan CLI

```bash
quick-convert --to pdf presentasi.pptx
quick-convert --to webp --out-dir ./hasil *.png
quick-convert --to pdf-merge --merged-name laporan foto1.png foto2.jpg
```
