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

import requests
from config import OLLAMA_URL, OLLAMA_MODEL, ARSEN_PERSONA
from tools.schema import TOOLS_SCHEMA, TOOL_FUNCTIONS

conversation_history = [
    {"role": "system", "content": ARSEN_PERSONA}
]

# Batas maksimal pesan di history (1 system + 10 pesan = 5 pasang user+assistant).
# Tanpa batas ini, history terus menumpuk → context window LLM penuh → jawaban
# mulai nggaco karena terlalu banyak context yang harus diproses (dan memakan memory yang bikin lambat).
MAX_HISTORY = 11

def _trim_history():
    """Potong history kalau sudah melebihi batas, pertahankan system prompt."""
    if len(conversation_history) > MAX_HISTORY:
        conversation_history[:] = [conversation_history[0]] + conversation_history[-10:]

def ask_llm(user_text: str) -> str:
    """
    Parameter:
    - user_text: hasil transkripsi dari stt_engine.transcribe()

    Return: teks jawaban FINAL dari LLM (setelah tool call selesai diproses
    kalau ada), siap dikirim ke tts_engine.
    """
    conversation_history.append({"role": "user", "content": user_text})
    _trim_history()
    return _call_ollama_with_tools()


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
            "options": {
                "temperature": 0.7,   # Cukup kreatif tapi nggak terlalu random/melenceng.
                "num_predict": 60,    # Batasi panjang jawaban (~1 kalimat, bikin LLM kilat mikirnya).
            },
        })
        data = response.json()
        message = data.get("message", {})

        # .get() dipakai (bukan langsung message["tool_calls"]) karena kalau
        # LLM TIDAK memilih manggil tool, key "tool_calls" ini biasanya tidak
        # ada sama sekali di response — .get() aman, return None kalau key
        # tidak ada, tanpa bikin program crash KeyError.
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            # LLM sudah kasih jawaban teks biasa (bukan minta tool)
            # → ini jawaban FINAL, simpan ke history dan selesai.
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
                # **function_args = "unpack" dictionary jadi keyword arguments.
                # Contoh: kalau function_args = {"location": "Jakarta"}, baris
                # ini setara dengan manggil get_weather(location="Jakarta")
                result = TOOL_FUNCTIONS[function_name](**function_args)
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
