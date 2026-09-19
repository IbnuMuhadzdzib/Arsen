"""
llm_client.py — Menghubungkan program ke Ollama (LLM lokal) yang jalan
sebagai server terpisah di background komputer kamu.

PENTING: file ini TIDAK menjalankan LLM secara langsung di dalam Python.
Ollama jalan sendiri sebagai aplikasi/server (lihat README.md), dan file ini
cuma mengirim HTTP request ke server itu — persis seperti manggil API
online, bedanya server-nya ada di komputer kamu sendiri (localhost),
jadi tidak ada biaya dan tidak butuh internet.
"""

import requests
from config import OLLAMA_URL, OLLAMA_MODEL, ARSEN_PERSONA

# conversation_history menyimpan seluruh percakapan sejak program dijalankan,
# supaya Arsen "ingat" konteks obrolan sebelumnya, bukan cuma menjawab pertanyaan
# terakhir tanpa tahu apa yang dibahas sebelumnya.
#
# Baris pertama selalu system prompt (persona Arsen) — role "system" adalah
# instruksi tersembunyi yang tidak "diucapkan" user, tapi membentuk cara LLM menjawab.
conversation_history = [
    {"role": "system", "content": ARSEN_PERSONA}
]

# Batas maksimal pesan di history (1 system + 10 pesan = 5 pasang user+assistant).
# Tanpa batas ini, history terus menumpuk → context window LLM penuh → jawaban
# mulai nggaco karena terlalu banyak context yang harus diproses.
MAX_HISTORY = 11


def _trim_history():
    """Potong history kalau sudah melebihi batas, pertahankan system prompt."""
    if len(conversation_history) > MAX_HISTORY:
        conversation_history[:] = [conversation_history[0]] + conversation_history[-10:]


def ask_llm(user_text: str) -> str:
    """
    Parameter:
    - user_text: hasil transkripsi dari stt_engine.transcribe()

    Return: teks jawaban dari LLM, siap dikirim ke tts_engine.
    """
    # Tambahkan pertanyaan user ke riwayat percakapan SEBELUM dikirim,
    # supaya request ini menyertakan konteks obrolan lengkap sampai saat ini.
    conversation_history.append({"role": "user", "content": user_text})

    # Trim history supaya nggak overflow context window LLM
    _trim_history()

    # requests.post mengirim HTTP POST request ke server Ollama.
    # json={...} otomatis mengubah dictionary Python ini jadi format JSON
    # yang dimengerti Ollama, dan set header Content-Type dengan benar.
    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "messages": conversation_history,
        "stream": False,   # False = tunggu jawaban lengkap sekaligus.
        "options": {
            "temperature": 0.7,   # Cukup kreatif tapi nggak terlalu random/melenceng.
                                  # Default Ollama bisa terlalu tinggi, bikin jawaban nggaco.
            "num_predict": 80,    # Batasi panjang jawaban (~1-2 kalimat).
                                  # Ini percakapan lisan, bukan esai.
        },
    })

    # .json() mengubah response HTTP (format teks JSON) jadi dictionary Python
    # supaya bisa diakses seperti data biasa.
    data = response.json()

    # Struktur response Ollama: {"message": {"role": "assistant", "content": "..."}}
    # — kita ambil isi jawabannya saja.
    reply_text = data["message"]["content"]

    # Simpan juga jawaban Arsen ke riwayat, supaya di pertanyaan berikutnya
    # LLM tahu apa yang sudah dia jawab sebelumnya.
    conversation_history.append({"role": "assistant", "content": reply_text})

    return reply_text

