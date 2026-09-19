"""
llm_client.py — Menghubungkan program ke Ollama (LLM lokal), SEKARANG dengan
dukungan Function Calling: LLM bisa "meminta" menjalankan fungsi Python
tertentu (cek cuaca, kontrol musik) alih-alih cuma menjawab pakai teks bebas.

CATATAN: struktur JSON response tool_calls di bawah ini mengikuti format yang
umum dipakai Ollama untuk model yang mendukung tool calling. Kalau ada error
soal key yang tidak ditemukan (KeyError), kemungkinan versi Ollama kamu sedikit
beda strukturnya — cek dengan print(data) untuk lihat struktur asli yang
dikembalikan, lalu sesuaikan key yang diakses di bawah.
"""

import re
import requests
from config import OLLAMA_URL, OLLAMA_MODEL, ARSEN_PERSONA
from tools.schema import TOOLS_SCHEMA, TOOL_FUNCTIONS
from memory_store import init_db, save_message, load_recent_messages

# Pastikan tabel database sudah siap sebelum dipakai — dipanggil sekali di
# sini (saat file ini di-import), bukan di main.py, supaya llm_client.py
# tetap "mandiri" (siapapun yang import file ini otomatis dapat memory yang
# udah siap, tanpa harus ingat manggil init_db() secara terpisah).
init_db()

conversation_history = [
    {"role": "system", "content": ARSEN_PERSONA}
]

# PRIME histori: begitu program baru nyala, tarik beberapa obrolan terakhir
# dari database dan masukkan ke conversation_history — supaya Arsen "nyambung"
# dari sesi sebelumnya, bukan mulai dari nol total tiap kali di-restart.
conversation_history.extend(load_recent_messages(limit=10))


def ask_llm(user_text: str) -> str:
    """
    Parameter:
    - user_text: hasil transkripsi dari stt_engine.transcribe()

    Return: teks jawaban FINAL dari LLM (setelah tool call selesai diproses
    kalau ada), siap dikirim ke tts_engine.
    """
    conversation_history.append({"role": "user", "content": user_text})
    save_message("user", user_text)  # simpan permanen ke database

    reply_text = _call_ollama_with_tools()

    save_message("assistant", reply_text)  # simpan permanen ke database
    return reply_text


def _call_ollama_with_tools() -> str:
    # Safety limit: mencegah loop tak berujung kalau LLM terus-menerus minta
    # tool call baru tanpa pernah kasih jawaban teks final (jarang terjadi,
    # tapi tanpa limit ini bisa bikin program "macet" selamanya).
    max_tool_iterations = 3

    for _ in range(max_tool_iterations):
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": conversation_history,
            "tools": TOOLS_SCHEMA,  # <- baris baru: kasih tau LLM tools apa aja yang ada
            "stream": False,
        })
        data = response.json()
        message = data["message"]

        # .get() dipakai (bukan langsung message["tool_calls"]) karena kalau
        # LLM TIDAK memilih manggil tool, key "tool_calls" ini biasanya tidak
        # ada sama sekali di response — .get() aman, return None kalau key
        # tidak ada, tanpa bikin program crash KeyError.
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            # FALLBACK: model kecil (seperti llama3.2:3b) kadang tidak pakai
            # mekanisme tool_calls resmi, tapi malah menulis MANUAL percobaan
            # format tool call sebagai teks jawaban biasa — kadang JSON-nya
            # bahkan rusak/tidak valid. Daripada dibacakan mentah-mentah lewat
            # TTS (kedengaran aneh banget di suara), kita coba deteksi pola
            # nama tool di teks itu pakai regex — regex dipilih (bukan
            # json.loads) karena lebih toleran terhadap JSON yang sedikit rusak.
            content = message.get("content") or ""
            match = re.search(r'"name"\s*:\s*"(\w+)"', content)

            if match and match.group(1) in TOOL_FUNCTIONS:
                fallback_tool_name = match.group(1)
                # Coba ekstrak argumen juga kalau formatnya kebetulan valid,
                # tapi kalau gagal (JSON rusak), tetap lanjut dengan argumen
                # kosong — banyak tool kita (get_weather, pause_music, dll)
                # punya fallback/default sendiri kalau argumen kosong.
                tool_calls = [{
                    "function": {"name": fallback_tool_name, "arguments": {}}
                }]

        if not tool_calls:
            # LLM sudah kasih jawaban teks biasa (bukan minta tool, dan bukan
            # juga pola fallback di atas) → ini jawaban FINAL.
            conversation_history.append(message)
            return message["content"]

        # --- LLM MEMINTA menjalankan satu atau lebih tool ---

        # Simpan dulu "permintaan tool call" dari LLM ke history — supaya di
        # request berikutnya, LLM ingat dia barusan minta apa (konteks penting
        # supaya dia nyambung waktu baca hasil tool-nya nanti).
        conversation_history.append(message)

        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            function_args = tool_call["function"]["arguments"]  # sudah berupa
                                                                   # dict, bukan
                                                                   # string JSON

            if function_name in TOOL_FUNCTIONS:
                try:
                    # **function_args = "unpack" dictionary jadi keyword
                    # arguments. Contoh: kalau function_args = {"location":
                    # "Jakarta"}, baris ini setara dengan manggil
                    # get_weather(location="Jakarta")
                    result = TOOL_FUNCTIONS[function_name](**function_args)
                except TypeError:
                    # Ini menangkap kasus seperti argumen WAJIB (contoh:
                    # song_name di play_song) ternyata tidak dikirim LLM sama
                    # sekali (sering terjadi di jalur fallback regex di atas,
                    # yang memang tidak bisa mengekstrak argumen dari JSON
                    # yang rusak) — daripada program crash, kasih pesan yang
                    # bisa "dipahami" LLM di iterasi berikutnya.
                    result = f"Tool '{function_name}' butuh informasi tambahan yang belum diberikan, coba tanya ulang ke user detailnya."
            else:
                # Jaga-jaga kalau LLM "berhalusinasi" manggil nama tool yang
                # nggak pernah kita daftarkan — daripada program crash,
                # kasih pesan yang bisa dipahami LLM di iterasi berikutnya
                result = f"Tool '{function_name}' tidak dikenali/tidak tersedia."

            # Kirim HASIL eksekusi tool kembali ke riwayat percakapan, dengan
            # role "tool" (bukan "user" atau "assistant") — role ini secara
            # khusus memberi tahu LLM "ini data hasil fungsi, bukan omongan
            # user biasa", supaya LLM tau harus merangkainya jadi jawaban,
            # bukan menganggapnya sebagai pertanyaan baru dari user.
            conversation_history.append({
                "role": "tool",
                "content": result,
            })

        # Tidak ada `return` di sini secara sengaja — loop `for` di paling luar
        # akan mengulang, mengirim ulang seluruh history (yang sekarang sudah
        # berisi hasil tool) ke LLM, supaya LLM merangkai hasil tool itu jadi
        # kalimat jawaban yang natural.

    # Kalau sampai baris ini artinya sudah 3x iterasi tapi LLM masih terus
    # minta tool call baru tanpa pernah kasih jawaban final — safety fallback.
    return "Maaf, saya kesulitan memproses permintaan itu."