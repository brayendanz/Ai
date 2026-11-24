# DevSentry AI

Asisten coding & AI assistant lengkap — berjalan sebagai website yang bisa
dibuka langsung di browser (hosting cloud), ditenagai Anthropic API (Claude).

## Status Fitur vs Roadmap

| # | Fitur | Status |
|---|---|---|
| 1-3 | AI Chat, Context, Conversation History (buat/buka/**ganti judul/hapus**) | ✅ Selesai |
| 4-8 | Code Generation, Explanation, Debugging, Language Detection, **Code Workspace** (editor + file manager multi-proyek, download ZIP) | ✅ Selesai |
| 9-11 | Document Upload/Reader/Analysis (PDF/DOCX/TXT/CSV/JSON, ringkas/tanya/bandingkan) | ✅ Selesai |
| 12-15 | **Skill Manager** (import GitHub/ZIP, validasi SKILL.md, aktifkan/nonaktifkan, AI menerapkan skill relevan) | ✅ Selesai |
| 16-19 | **Plugin Manager** (import GitHub/ZIP, validasi plugin.json, aktifkan/nonaktifkan) | ✅ Selesai — **versi deklaratif**, lihat catatan keamanan di bawah |
| 20 | **AI Memory** (tambah/lihat/hapus fakta, otomatis disuntikkan ke percakapan) | ✅ Selesai |
| 21-22 | **Knowledge Base & RAG** (tandai dokumen sebagai KB, retrieval otomatis + sitasi sumber) | ✅ Selesai — retrieval berbasis keyword/TF-IDF ringan, tanpa API embedding tambahan |
| 23 | **Model Manager** (pilih model Claude aktif: Haiku/Sonnet/Opus) | ✅ Selesai |
| 24-25 | **AI Settings & User Settings** (temperature, panjang jawaban, gaya, bahasa, nama, tema, hapus riwayat) | ✅ Selesai |
| 26 | **Multi-Model Intelligence** (bandingkan jawaban beberapa model sekaligus) | ✅ Selesai |
| 27 | **AI Agent** (planning bertahap + approval sebelum eksekusi) | ✅ Selesai — tools terbatas (create_file, search_knowledge) demi keamanan |
| 28 | AI Model Training | ❌ **Di luar scope** — lihat penjelasan di bawah |

## Kenapa AI Model Training Tidak Dibangun

Fine-tuning/training model sungguhan butuh infrastruktur GPU khusus (cluster
training, dataset pipeline besar, biaya compute signifikan) — ini kelas
infrastruktur yang sama sekali berbeda dari aplikasi web biasa seperti
DevSentry AI, dan tidak bisa berjalan di hosting Flask/Render/Railway biasa.
Kalau nanti dibutuhkan, opsi realistis: integrasi ke layanan fine-tuning
pihak ketiga (mis. lewat Anthropic Console / AWS Bedrock / Vertex AI) sebagai
langkah terpisah di luar aplikasi ini, bukan fitur in-app.

## Catatan Keamanan Penting: Plugin Manager

Plugin di DevSentry AI **tidak menjalankan kode bebas di server**. plugin.json
hanya boleh berisi metadata + `instructions` (teks instruksi tambahan untuk
AI) — mirip "system prompt modular", bukan kode yang dieksekusi. Ini sengaja
dibuat begini: mengizinkan siapa pun mengunggah "plugin" berisi kode untuk
dieksekusi langsung di server akan membuka celah Remote Code Execution (RCE)
— siapa saja di internet bisa menjalankan kode apa pun di server-mu. Kalau
suatu saat benar-benar butuh plugin yang menjalankan kode, itu harus dibatasi
ketat untuk admin saja dan dijalankan di sandbox/container terpisah sekali
pakai — bukan arsitektur yang aman untuk dibuka ke pengunjung umum.

**Default**: Skill & Plugin Manager hanya bisa dikelola oleh admin (perlu
`ADMIN_ACCESS_CODE`, login di `/admin/login`). Untuk membuka ke semua
pengunjung (sesuai permintaan awal), set `SKILLS_PLUGINS_PUBLIC=true` — tapi
pahami risikonya: siapa pun bisa menambah "kepribadian"/instruksi ke AI-mu,
yang bisa disalahgunakan untuk prompt injection terhadap pengunjung lain.

## Fitur Lengkap

| Mode/Tab | Fungsi |
|---|---|
| **Chat** | 6 mode (Umum, Dasar Coding, Website Builder, Website Config, Security Defensif, Security Edukasi) + Document Analysis, histori per percakapan, multi-model compare |
| **Code Workspace** | Multi-proyek, multi-file, editor kode, simpan/hapus, download ZIP |
| **Skills** | Import dari GitHub/ZIP, deteksi SKILL.md, validasi, aktifkan/nonaktifkan/hapus |
| **Plugins** | Import dari GitHub/ZIP, deteksi plugin.json, validasi, aktifkan/nonaktifkan/hapus (deklaratif) |
| **Memory** | Tambah/lihat/hapus fakta yang diingat AI lintas sesi |
| **Agent** | Buat rencana bertahap dari satu tujuan, approve/skip tiap langkah |
| **Settings** | Model Manager, AI Settings (kreativitas/panjang/gaya/bahasa), User Settings (nama/tema/hapus riwayat) |

## Cara Deploy (tanpa terminal lokal)

### Render.com (disarankan)

1. Upload folder ini ke repository GitHub.
2. https://render.com → "New +" → "Web Service" → hubungkan repo.
3. Render otomatis pakai `Dockerfile`.
4. Di tab **Environment**, tambahkan minimal:
   - `ANTHROPIC_API_KEY`
   - `SECRET_KEY`
   - (opsional) `LAB_ACCESS_CODE`, `ADMIN_ACCESS_CODE`, `SKILLS_PLUGINS_PUBLIC`
5. Deploy. Dapat URL publik otomatis.

### Railway.app

Sama seperti di atas: "New Project" → "Deploy from GitHub repo" → isi
Environment Variables di tab **Variables**.

## Environment Variables

Lihat `.env.example` untuk daftar lengkap.

## Struktur Folder

```
devsentry_ai/
├── app.py                     # Entry point Flask + semua route API
├── config.py                   # Konfigurasi (dari environment variables)
├── requirements.txt
├── Dockerfile / Procfile
├── .env.example
├── modules/
│   ├── ai_client.py            # Komunikasi dengan Anthropic API (+ multi-model)
│   ├── personas.py             # System prompt per mode
│   ├── database.py             # Semua tabel: conversations, documents, skills, plugins, memory, settings, agent_tasks
│   ├── documents.py             # Ekstraksi teks PDF/DOCX/TXT/CSV/JSON
│   ├── code_workspace.py        # File manager multi-proyek
│   ├── skill_manager.py         # Import & validasi Skill (SKILL.md)
│   ├── plugin_manager.py        # Import & validasi Plugin (plugin.json) — deklaratif
│   ├── knowledge_base.py        # Chunking + retrieval RAG ringan (keyword/TF-IDF)
│   ├── memory.py                # AI Memory (fakta lintas sesi)
│   ├── context_builder.py       # Menggabungkan Skill+Plugin+Memory+RAG ke system prompt
│   ├── agent.py                 # AI Agent: planning + approval-gated execution
│   └── security/
│       ├── defensive_snippets.py
│       └── vuln_lab.py
├── templates/index.html         # UI tab: Chat, Workspace, Skills, Plugins, Memory, Agent, Settings
├── static/css/style.css
├── static/js/app.js
└── workspace/
    ├── documents/                # File dokumen yang diunggah
    └── projects/                 # Proyek Code Workspace
```

(Folder `skills_store/` dan `plugins_store/` otomatis dibuat di root project saat Skill/Plugin pertama diimpor.)

## Catatan Hosting (Filesystem Sementara)

Banyak platform hosting gratis me-reset filesystem saat redeploy. Yang akan
hilang: `devsentry.db` (riwayat, skill, plugin, memory, settings), dokumen
di `workspace/documents/`, dan proyek di `workspace/projects/`. Untuk
produksi jangka panjang: gunakan Persistent Disk (Render) atau migrasi ke
PostgreSQL + object storage (S3-compatible).

## Keamanan Bawaan (ringkasan)

- API key tidak pernah hardcode — selalu dari environment variable.
- Path traversal diblokir di semua fitur file (Document upload, Code Workspace, Skill/Plugin ZIP extraction — termasuk proteksi zip-slip).
- Lab kerentanan & Skill/Plugin Manager dikunci kode akses secara default.
- Plugin bersifat deklaratif — tidak ada eksekusi kode pihak ketiga di server.
- AI Agent hanya punya akses ke tools yang eksplisit didefinisikan (bukan shell/kode bebas), dan tindakan penting butuh approval.
