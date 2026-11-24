"""
Ekstraksi teks & struktur dari dokumen yang diunggah pengguna.
Mendukung: PDF, DOCX, TXT, CSV, JSON.
"""

import csv
import io
import json
import os

import config

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv", "json"}


class DocumentError(Exception):
    pass


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[1].lower()


def extract_text(filepath: str, ext: str):
    """
    Mengembalikan (text, meta_dict).
    text: teks penuh (atau representasi teks) dari dokumen.
    meta_dict: info struktur (jumlah halaman/baris/kolom/dll) untuk ditampilkan ke pengguna.
    """
    if ext == "pdf":
        return _extract_pdf(filepath)
    if ext == "docx":
        return _extract_docx(filepath)
    if ext == "txt":
        return _extract_txt(filepath)
    if ext == "csv":
        return _extract_csv(filepath)
    if ext == "json":
        return _extract_json(filepath)
    raise DocumentError(f"Format .{ext} tidak didukung.")


def _extract_pdf(filepath):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise DocumentError("Library pypdf belum terinstall di server.")

    reader = PdfReader(filepath)
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    text = "\n\n".join(pages_text)
    meta = {"jenis": "PDF", "jumlah_halaman": len(reader.pages)}
    return text, meta


def _extract_docx(filepath):
    try:
        import docx
    except ImportError:
        raise DocumentError("Library python-docx belum terinstall di server.")

    doc = docx.Document(filepath)
    parts = []
    headings = []
    for para in doc.paragraphs:
        if not para.text.strip():
            continue
        if para.style.name.startswith("Heading"):
            headings.append(para.text.strip())
            parts.append(f"\n## {para.text.strip()}\n")
        else:
            parts.append(para.text)

    # Sertakan isi tabel juga, jika ada
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            parts.append(" | ".join(cells))

    text = "\n".join(parts)
    meta = {
        "jenis": "DOCX",
        "jumlah_paragraf": len(doc.paragraphs),
        "jumlah_tabel": len(doc.tables),
        "heading": headings[:20],
    }
    return text, meta


def _extract_txt(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    meta = {"jenis": "TXT", "jumlah_karakter": len(text)}
    return text, meta


def _extract_csv(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return "", {"jenis": "CSV", "jumlah_baris": 0, "kolom": []}

    header = rows[0]
    data_rows = rows[1:]

    # Batasi jumlah baris yang dikirim ke AI supaya tidak membengkak
    MAX_ROWS = 300
    preview_rows = data_rows[:MAX_ROWS]

    lines = [", ".join(header)]
    for r in preview_rows:
        lines.append(", ".join(r))
    text = "\n".join(lines)

    if len(data_rows) > MAX_ROWS:
        text += f"\n\n[... {len(data_rows) - MAX_ROWS} baris lainnya dipotong untuk ringkasan ini ...]"

    meta = {"jenis": "CSV", "jumlah_baris": len(data_rows), "kolom": header}
    return text, meta


def _extract_json(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    text = json.dumps(data, indent=2, ensure_ascii=False)
    MAX_CHARS = 20000
    truncated = len(text) > MAX_CHARS
    if truncated:
        text = text[:MAX_CHARS] + "\n...(dipotong)..."

    top_keys = list(data.keys()) if isinstance(data, dict) else None
    meta = {
        "jenis": "JSON",
        "tipe_root": type(data).__name__,
        "top_level_keys": top_keys,
        "dipotong": truncated,
    }
    return text, meta


def truncate_for_ai(text: str, max_chars: int = None) -> str:
    max_chars = max_chars or config.MAX_DOC_CHARS_FOR_AI
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[... dipotong, total {len(text)} karakter ...]"
