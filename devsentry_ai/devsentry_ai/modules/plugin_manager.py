"""
Plugin Manager — import dari GitHub/ZIP, deteksi & validasi plugin.json.

CATATAN KEAMANAN PENTING:
Plugin di sini BERSIFAT DEKLARATIF, bukan kode yang dieksekusi bebas di server.
plugin.json hanya boleh berisi metadata + instruksi tambahan (system prompt
tambahan) yang akan disisipkan ke AI saat plugin itu aktif — mirip "system
prompt modular". Ini sengaja dibuat begini karena situs ini publik: mengizinkan
siapa pun mengunggah "plugin" berisi kode untuk dieksekusi di server akan
menjadi celah Remote Code Execution. Jika suatu saat kamu butuh plugin yang
benar-benar menjalankan kode, itu HARUS dibatasi hanya untuk admin (lihat
config.SKILLS_PLUGINS_PUBLIC) dan dijalankan di sandbox terpisah (container
sekali pakai), bukan di proses server utama.

Format plugin.json yang didukung:
{
  "name": "...",
  "version": "1.0.0",
  "description": "...",
  "instructions": "Instruksi tambahan untuk AI saat plugin ini aktif",
  "permissions": []   # reserved untuk versi mendatang, belum dieksekusi
}
"""

import io
import json
import os
import re
import shutil
import uuid
import zipfile

import requests
import config


class PluginError(Exception):
    pass


REQUIRED_FIELDS = ["name", "version", "description"]


def ensure_dirs():
    os.makedirs(config.PLUGINS_DIR, exist_ok=True)


def _find_manifest_files(root_dir):
    found = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.lower() == "plugin.json":
                found.append(os.path.join(dirpath, fn))
    return found


def validate_manifest(manifest_path):
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return False, f"plugin.json tidak bisa dibaca: {e}", None

    missing = [f for f in REQUIRED_FIELDS if f not in manifest]
    if missing:
        return False, f"Field wajib hilang: {', '.join(missing)}", None

    if not isinstance(manifest.get("name"), str) or not manifest["name"].strip():
        return False, "Field 'name' tidak valid", None

    # instructions opsional, tapi kalau ada harus string dan dibatasi panjangnya
    instructions = manifest.get("instructions", "")
    if not isinstance(instructions, str):
        return False, "Field 'instructions' harus berupa teks", None
    if len(instructions) > 8000:
        return False, "Field 'instructions' terlalu panjang (maks 8000 karakter)", None

    return True, "Valid", manifest


def import_from_zip(file_storage):
    ensure_dirs()
    data = file_storage.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise PluginError("File ZIP tidak valid.")

    temp_extract = os.path.join(config.PLUGINS_DIR, f"_tmp_{uuid.uuid4().hex}")
    os.makedirs(temp_extract, exist_ok=True)

    for member in zf.namelist():
        member_path = os.path.abspath(os.path.join(temp_extract, member))
        if not member_path.startswith(os.path.abspath(temp_extract)):
            shutil.rmtree(temp_extract, ignore_errors=True)
            raise PluginError("ZIP berisi path yang tidak aman.")
    zf.extractall(temp_extract)

    return _import_from_extracted_root(temp_extract, source="zip")


def import_from_github(github_url: str):
    ensure_dirs()
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(\.git)?/?$", github_url.strip())
    if not match:
        raise PluginError("URL GitHub tidak valid. Gunakan format https://github.com/user/repo")

    owner, repo = match.group(1), match.group(2)
    last_error = None

    for branch in ["main", "master"]:
        zip_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
        try:
            resp = requests.get(zip_url, timeout=30)
            if resp.status_code == 200:
                temp_extract = os.path.join(config.PLUGINS_DIR, f"_tmp_{uuid.uuid4().hex}")
                os.makedirs(temp_extract, exist_ok=True)
                zf = zipfile.ZipFile(io.BytesIO(resp.content))
                zf.extractall(temp_extract)
                return _import_from_extracted_root(temp_extract, source=github_url)
            last_error = f"HTTP {resp.status_code}"
        except requests.exceptions.RequestException as e:
            last_error = str(e)

    raise PluginError(f"Gagal mengunduh repository dari GitHub ({last_error}).")


def _import_from_extracted_root(temp_extract, source):
    from . import database

    manifest_files = _find_manifest_files(temp_extract)
    if not manifest_files:
        shutil.rmtree(temp_extract, ignore_errors=True)
        raise PluginError("Tidak ditemukan file plugin.json di dalam repository/ZIP ini.")

    imported = []
    for manifest_path in manifest_files:
        is_valid, message, manifest = validate_manifest(manifest_path)
        if not is_valid:
            continue

        plugin_folder = os.path.dirname(manifest_path)
        final_folder = os.path.join(config.PLUGINS_DIR, uuid.uuid4().hex)
        shutil.copytree(plugin_folder, final_folder)

        plugin_id = database.add_plugin(
            name=manifest["name"],
            version=manifest.get("version", "0.0.0"),
            description=manifest.get("description", ""),
            manifest_json=json.dumps(manifest, ensure_ascii=False),
            folder_path=final_folder,
        )
        imported.append({"id": plugin_id, "name": manifest["name"]})

    shutil.rmtree(temp_extract, ignore_errors=True)

    if not imported:
        raise PluginError("plugin.json ditemukan tapi tidak ada yang valid.")

    return imported
