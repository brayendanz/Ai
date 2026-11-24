"""
Code Workspace — file manager sederhana untuk membuat/mengedit/menghapus
file dalam sebuah "proyek" (folder) di dalam PROJECTS_DIR.
Semua path divalidasi supaya tidak bisa keluar dari PROJECTS_DIR (anti path traversal).
"""

import os
import shutil
import config


class WorkspaceError(Exception):
    pass


def _safe_join(*parts):
    path = os.path.abspath(os.path.join(config.PROJECTS_DIR, *parts))
    base = os.path.abspath(config.PROJECTS_DIR)
    if not (path == base or path.startswith(base + os.sep)):
        raise WorkspaceError("Path tidak diizinkan (di luar workspace).")
    return path


def ensure_dirs():
    os.makedirs(config.PROJECTS_DIR, exist_ok=True)


def list_projects():
    ensure_dirs()
    return sorted([d for d in os.listdir(config.PROJECTS_DIR)
                   if os.path.isdir(os.path.join(config.PROJECTS_DIR, d))])


def create_project(project_name):
    if not project_name or any(c in project_name for c in "/\\.."):
        raise WorkspaceError("Nama proyek tidak valid.")
    path = _safe_join(project_name)
    os.makedirs(path, exist_ok=True)
    return project_name


def delete_project(project_name):
    path = _safe_join(project_name)
    if os.path.isdir(path):
        shutil.rmtree(path)


def list_files(project_name):
    """Mengembalikan daftar relative path semua file dalam proyek."""
    project_path = _safe_join(project_name)
    if not os.path.isdir(project_path):
        return []
    files = []
    for root, _, filenames in os.walk(project_path):
        for fn in filenames:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, project_path)
            files.append(rel.replace(os.sep, "/"))
    return sorted(files)


def read_file(project_name, rel_path):
    path = _safe_join(project_name, rel_path)
    if not os.path.isfile(path):
        raise WorkspaceError("File tidak ditemukan.")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_file(project_name, rel_path, content):
    if ".." in rel_path.split("/"):
        raise WorkspaceError("Path tidak valid.")
    size_mb = len(content.encode("utf-8")) / (1024 * 1024)
    if size_mb > config.MAX_WORKSPACE_FILE_SIZE_MB:
        raise WorkspaceError(f"File melebihi batas {config.MAX_WORKSPACE_FILE_SIZE_MB} MB.")

    path = _safe_join(project_name, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def delete_file(project_name, rel_path):
    path = _safe_join(project_name, rel_path)
    if os.path.isfile(path):
        os.remove(path)


def zip_project(project_name, dest_path_no_ext):
    project_path = _safe_join(project_name)
    if not os.path.isdir(project_path):
        raise WorkspaceError("Proyek tidak ditemukan.")
    return shutil.make_archive(dest_path_no_ext, "zip", project_path)
