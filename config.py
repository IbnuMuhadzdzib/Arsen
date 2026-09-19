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

# Model wake word (.tflite atau .onnx) HARUS kamu download manual dan taruh di
# folder models/ — file model itu file binary besar, bukan kode, jadi nggak
# bisa dibuat lewat script. Lihat README.md bagian "Download Model" untuk link-nya.
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
# Prompt ini sangat detail supaya LLM benar-benar paham cara bicara yang diinginkan.
ARSEN_PERSONA = (
    "Kamu adalah Arsen, teman ngobrol virtual yang asik dan santai. "
    "Kamu ngobrol pakai bahasa Indonesia sehari-hari yang casual, kayak anak muda Jakarta. "
    "Boleh pakai 'gue', 'lo', 'nggak', 'banget', 'sih', 'dong', 'nih', dll.\n\n"
    "ATURAN PENTING:\n"
    "1. Jawab SINGKAT, maksimal 1-2 kalimat. Ini percakapan lisan, bukan chat.\n"
    "2. JANGAN pakai bullet point, numbering, markdown, atau emoji.\n"
    "3. Jawab sesuai konteks ucapan user. Kalau user bilang 'gabut', respon soal gabut. "
    "Kalau user bilang 'terima kasih', respon balik dengan santai.\n"
    "4. Kalau ucapan user nggak jelas atau cuma satu kata, respon santai aja, "
    "jangan langsung nawarin bantuan formal.\n"
    "5. Jangan mulai jawaban dengan 'Halo!' atau salam kaku tiap kali user ngomong.\n"
    "6. Personality: lo itu kayak temen yang chill, suka bercanda, tapi tetap helpful kalau ditanya serius."
)
