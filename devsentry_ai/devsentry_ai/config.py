"""
Konfigurasi global DevSentry AI - versi hosting online.

SEMUA nilai sensitif (API key, kode akses lab) diambil dari Environment
Variables yang kamu set di dashboard layanan hosting (Render/Railway/dsb),
BUKAN ditulis langsung di file ini. Jangan commit API key ke git.
"""

import os

# --- AI Provider ---
# "anthropic" = pakai Claude API (direkomendasikan untuk hosting online,
#   tidak perlu install model apa pun di server).
AI_PROVIDER = os.environ.get("AI_PROVIDER", "anthropic")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

# --- Flask ---
SECRET_KEY = os.environ.get("SECRET_KEY", "ganti-ini-lewat-env-var-di-hosting")
HOST = "0.0.0.0"  # wajib 0.0.0.0 untuk platform hosting (Render/Railway/dll)
PORT = int(os.environ.get("PORT", 5000))  # kebanyakan platform inject PORT otomatis
DEBUG = False

# --- Database riwayat chat ---
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "devsentry.db"))

# --- Workspace tempat AI membuat/menulis file proyek ---
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")

# --- Document Analysis ---
DOCUMENTS_DIR = os.path.join(WORKSPACE_DIR, "documents")
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 15))
# Batas karakter per dokumen yang dikirim ke AI (menjaga biaya & batas token)
MAX_DOC_CHARS_FOR_AI = int(os.environ.get("MAX_DOC_CHARS_FOR_AI", 40000))

# --- Code Workspace (file manager & editor) ---
PROJECTS_DIR = os.path.join(WORKSPACE_DIR, "projects")
MAX_WORKSPACE_FILE_SIZE_MB = int(os.environ.get("MAX_WORKSPACE_FILE_SIZE_MB", 5))

# --- Skill & Plugin Manager ---
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills_store")
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins_store")
# Siapa yang boleh import/kelola Skill & Plugin.
# True = terbuka untuk semua pengunjung (TIDAK direkomendasikan di situs publik).
# False = hanya yang tahu ADMIN_ACCESS_CODE.
SKILLS_PLUGINS_PUBLIC = os.environ.get("SKILLS_PLUGINS_PUBLIC", "false").lower() == "true"
ADMIN_ACCESS_CODE = os.environ.get("ADMIN_ACCESS_CODE", "")

# --- Model Manager: model Claude yang tersedia untuk dipilih pengguna ---
AVAILABLE_MODELS = [
    {"id": "claude-haiku-4-5", "label": "Claude Haiku (cepat & hemat)"},
    {"id": "claude-sonnet-4-5", "label": "Claude Sonnet (seimbang, default)"},
    {"id": "claude-opus-4-1", "label": "Claude Opus (paling mendalam)"},
]

# --- Lab Keamanan (edukatif) ---
# Karena situs ini online/publik, lab kerentanan WAJIB dikunci dengan kode akses
# supaya tidak disalahgunakan orang lain sebagai alat menyerang pihak ketiga
# (misalnya mengirim link payload XSS ke korban). Set LAB_ACCESS_CODE di env var
# hosting-mu. Kalau kosong, lab otomatis nonaktif.
SECURITY_LAB_ENABLED = bool(os.environ.get("LAB_ACCESS_CODE", ""))
LAB_ACCESS_CODE = os.environ.get("LAB_ACCESS_CODE", "")
