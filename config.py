"""
config.py — Tempat semua "angka ajaib" dan pengaturan project dikumpulkan.

KENAPA FILE INI ADA SENDIRI (terpisah dari main.py)?
Supaya kalau kamu mau ganti model, path, atau parameter apapun, kamu tinggal
edit di SATU file ini — tanpa perlu buka-buka semua file lain nyari angka yang
harus diubah. Ini praktik umum di software engineering, namanya "centralized config".
"""

import os

# --- PATH / LOKASI FOLDER ---
# os.path.dirname(__file__) = folder tempat config.py ini berada.
# Fungsinya: supaya path selalu benar walaupun kamu jalanin script dari folder
# lain (misal dari luar folder project) — nggak hardcode path absolut.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# os.path.join menggabungkan path dengan separator yang benar sesuai OS
# (Windows pakai backslash \, Mac/Linux pakai forward slash /) — kalau digabung
# manual pakai string "models/" + nama_file, bisa error di Windows.
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Model wake word (.onnx) HARUS kamu download manual dan taruh di folder models/ —
# file model itu file binary besar, bukan kode, jadi nggak bisa dibuat lewat script.
# Pakai format .onnx (bukan .tflite) karena tflite-runtime tidak punya installer
# resmi untuk Windows — openWakeWord otomatis pakai onnxruntime untuk model .onnx,
# dan onnxruntime sudah ter-install lewat dependency faster-whisper.
WAKE_WORD_MODEL_PATH = os.path.join(MODELS_DIR, "hey_jarvis_v0.1.onnx")
WAKE_WORD_THRESHOLD = 0.5  # Skor minimal (0.0-1.0) supaya dianggap "wake word terdeteksi".
                           # Makin rendah = makin sensitif (tapi rawan salah deteksi).
                           # Makin tinggi = makin strict (tapi kadang nggak kedengeran).
                           # 0.5 adalah titik tengah yang wajar untuk mulai testing.

# Model suara Piper TTS — juga didownload manual, taruh di models/
TTS_VOICE_MODEL_PATH = os.path.join(MODELS_DIR, "id_ID-news_tts-medium.onnx")

# Lokasi file piper.exe (standalone executable, bukan package Python) —
# didownload manual dari GitHub releases Piper, ditaruh di folder piper/
PIPER_EXE_PATH = os.path.join(BASE_DIR, "piper", "piper.exe")

# --- PENGATURAN AUDIO ---
SAMPLE_RATE = 16000   # 16000 Hz = standar untuk kebanyakan model speech AI (Whisper,
                       # openWakeWord, Silero VAD semua dilatih dengan sample rate ini).
                       # Kalau mic kamu rekam di sample rate lain, hasil ke model AI bisa
                       # kacau — makanya angka ini harus konsisten di semua komponen.
CHANNELS = 1           # 1 = mono (satu jalur suara). Model speech AI nggak butuh stereo,
                       # jadi mono lebih hemat resource tanpa mengurangi kualitas deteksi.

# --- PENGATURAN LLM (Ollama) ---
OLLAMA_URL = "http://localhost:11434/api/chat"
# "localhost:11434" karena Ollama jalan sebagai server lokal di komputer kamu sendiri
# (bukan di internet) — 11434 adalah port default yang dipakai Ollama.
OLLAMA_MODEL = "llama3.2:3b"

# System prompt = instruksi "kepribadian" yang dikirim ke LLM setiap kali chat,
# supaya jawabannya konsisten seperti karakter Arsen, bukan jawaban generic.
ARSEN_PERSONA = (
    "Kamu adalah Arsen, teman ngobrol virtual yang asik dan santai. "
    "Kamu ngobrol pakai bahasa Indonesia sehari-hari yang casual, kayak anak muda Jakarta. "
    "Boleh pakai 'gue', 'lo', 'nggak', 'banget', 'sih', 'dong', 'nih', dll.\n\n"
    "ATURAN PENTING:\n"
    "1. Jawab SINGKAT, maksimal 1-2 kalimat. Ini percakapan lisan, bukan chat.\n"
    "2. JANGAN pakai bullet point, numbering, markdown, atau emoji.\n"
    "3. Jawab sesuai konteks ucapan user. Kalau ucapan user nggak jelas atau cuma "
    "   satu kata, respon santai aja.\n"
    "4. JANGAN PERNAH merespon dengan nge-print struktur JSON mentah (seperti "
    "   {\"name\": \"get_weather\"}). Jika kamu ingin menggunakan alat pembantu "
    "   seperti mengecek cuaca, gunakan function calling yang disediakan sistem tanpa "
    "   menuliskannya di teks jawaban.\n"
    "5. Kalau user bertanya soal cuaca dengan cara apapun (termasuk tanpa "
    "   menyebutkan nama kota), SELALU panggil tool get_weather — jangan pernah "
    "   menjawab dengan teks biasa minta klarifikasi lokasi, cukup panggil tool "
    "   itu dengan location dikosongkan."
)

# --- FASE 2: FUNCTION CALLING ---

# Daftar di openweathermap.org/api (tier gratis) untuk dapat API key ini.
# String kosong sengaja dibiarkan sebagai placeholder — WAJIB diisi sebelum
# fitur cuaca bisa jalan, program akan error kalau ini masih kosong.
OPENWEATHER_API_KEY = ""

# Lokasi default kalau kamu nanya cuaca TANPA sebut nama kota spesifik
# (misal cuma bilang "cuaca hari ini?", bukan "cuaca di Bandung?").
# GANTI ke kota kamu sendiri. Format: "NamaKota,KodeNegara" (ID = Indonesia).
DEFAULT_LOCATION = "Bekasi,ID"

# Dari Spotify Developer Dashboard (developer.spotify.com/dashboard) — buat
# "App" baru di situ untuk dapat Client ID & Client Secret ini.
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""

# Redirect URI ini HARUS persis sama dengan yang kamu daftarkan di Spotify
# Developer Dashboard saat setup App (lihat README.md) — Spotify menolak
# request kalau URI-nya tidak cocok persis, ini bagian dari keamanan OAuth.
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

# "Scope" = izin akses apa aja yang diminta ke akun Spotify kamu. Kita cuma
# minta izin kontrol playback (play/pause/lihat status), TIDAK minta akses ke
# data lain (playlist pribadi, riwayat, dll) — prinsip least privilege, minta
# akses seperlunya aja.
SPOTIFY_SCOPE = "user-modify-playback-state user-read-playback-state"