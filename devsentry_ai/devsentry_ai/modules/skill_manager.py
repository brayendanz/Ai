"""
Skill Manager — mengimpor "Skill" (folder instruksi berisi SKILL.md, mirip
format Skill Claude) dari URL GitHub atau file ZIP, memvalidasi strukturnya,
lalu menyimpannya supaya bisa diaktifkan/nonaktifkan dan dipakai AI.
"""

import io
import os
import re
import shutil
import uuid
import zipfile

import requests
import config


class SkillError(Exception):
    pass


def ensure_dirs():
    os.makedirs(config.SKILLS_DIR, exist_ok=True)


def _parse_skill_md(content: str):
    """Ambil 'name' dan 'description' dari frontmatter YAML sederhana di SKILL.md."""
    name = None
    description = None
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        name_match = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
        desc_match = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip('"\'')
        if desc_match:
            description = desc_match.group(1).strip().strip('"\'')
    if not name:
        # fallback: ambil heading pertama
        h_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        name = h_match.group(1).strip() if h_match else "Skill Tanpa Nama"
    if not description:
        description = "(Tidak ada deskripsi di SKILL.md)"
    return name, description


def _find_skill_md_files(root_dir):
    """Cari semua SKILL.md di dalam folder (bisa lebih dari satu skill per repo)."""
    found = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.upper() == "SKILL.MD":
                found.append(os.path.join(dirpath, fn))
    return found


def validate_skill_folder(skill_folder):
    """Validasi dasar: ada SKILL.md, bisa dibaca, frontmatter wajar."""
    skill_md_path = os.path.join(skill_folder, "SKILL.md")
    if not os.path.isfile(skill_md_path):
        # cari case-insensitive
        for fn in os.listdir(skill_folder):
            if fn.upper() == "SKILL.MD":
                skill_md_path = os.path.join(skill_folder, fn)
                break
        else:
            return False, "Tidak ditemukan file SKILL.md", None, None, None

    with open(skill_md_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if len(content.strip()) < 10:
        return False, "SKILL.md kosong atau terlalu pendek", None, None, None

    name, description = _parse_skill_md(content)
    return True, "Valid", name, description, content


def import_from_zip(file_storage):
    """file_storage: objek file Flask (request.files['file'])."""
    ensure_dirs()
    data = file_storage.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise SkillError("File ZIP tidak valid.")

    temp_extract = os.path.join(config.SKILLS_DIR, f"_tmp_{uuid.uuid4().hex}")
    os.makedirs(temp_extract, exist_ok=True)

    # cegah zip-slip: pastikan semua anggota tetap di dalam temp_extract
    for member in zf.namelist():
        member_path = os.path.abspath(os.path.join(temp_extract, member))
        if not member_path.startswith(os.path.abspath(temp_extract)):
            shutil.rmtree(temp_extract, ignore_errors=True)
            raise SkillError("ZIP berisi path yang tidak aman.")
    zf.extractall(temp_extract)

    return _import_from_extracted_root(temp_extract, source="zip")


def import_from_github(github_url: str):
    """
    Mendukung URL repo biasa, mis. https://github.com/user/repo
    Mengunduh branch default sebagai ZIP lewat codeload.github.com.
    """
    ensure_dirs()
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(\.git)?/?$", github_url.strip())
    if not match:
        raise SkillError("URL GitHub tidak valid. Gunakan format https://github.com/user/repo")

    owner, repo = match.group(1), match.group(2)
    branches_to_try = ["main", "master"]
    last_error = None

    for branch in branches_to_try:
        zip_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
        try:
            resp = requests.get(zip_url, timeout=30)
            if resp.status_code == 200:
                temp_extract = os.path.join(config.SKILLS_DIR, f"_tmp_{uuid.uuid4().hex}")
                os.makedirs(temp_extract, exist_ok=True)
                zf = zipfile.ZipFile(io.BytesIO(resp.content))
                zf.extractall(temp_extract)
                return _import_from_extracted_root(temp_extract, source=github_url)
            last_error = f"HTTP {resp.status_code}"
        except requests.exceptions.RequestException as e:
            last_error = str(e)

    raise SkillError(f"Gagal mengunduh repository dari GitHub ({last_error}).")


def _import_from_extracted_root(temp_extract, source):
    """Cari semua SKILL.md di dalam hasil ekstraksi, validasi, pindahkan tiap skill ke folder permanen."""
    from . import database

    skill_md_files = _find_skill_md_files(temp_extract)
    if not skill_md_files:
        shutil.rmtree(temp_extract, ignore_errors=True)
        raise SkillError("Tidak ditemukan file SKILL.md di dalam repository/ZIP ini.")

    imported = []
    for skill_md_path in skill_md_files:
        skill_folder = os.path.dirname(skill_md_path)
        is_valid, message, name, description, content = validate_skill_folder(skill_folder)
        if not is_valid:
            continue

        final_folder = os.path.join(config.SKILLS_DIR, uuid.uuid4().hex)
        shutil.copytree(skill_folder, final_folder)

        skill_id = database.add_skill(
            name=name,
            description=description,
            source=source,
            folder_path=final_folder,
            skill_md=content,
        )
        imported.append({"id": skill_id, "name": name, "description": description})

    shutil.rmtree(temp_extract, ignore_errors=True)

    if not imported:
        raise SkillError("SKILL.md ditemukan tapi tidak ada yang valid.")

    return imported
