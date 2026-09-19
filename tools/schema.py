"""
schema.py — Dua hal penting di file ini:

1. TOOLS_SCHEMA: daftar "tools" dalam format JSON yang dikirim ke LLM setiap
   kali chat, supaya LLM TAHU tools apa aja yang tersedia dan kapan boleh
   memanggilnya. Ini semacam "daftar menu" yang dibaca LLM.

2. TOOL_FUNCTIONS: dictionary yang menghubungkan NAMA tool (string, yang
   disebut LLM) ke FUNGSI PYTHON asli yang benar-benar dieksekusi. Tanpa ini,
   kita harus nulis if/elif panjang tiap kali LLM minta tool tertentu.
"""

from tools.weather_tool import get_weather
from tools.music_tool import play_song, pause_music, resume_music

# Format skema ini mengikuti standar function calling yang dipahami Ollama
# untuk model yang mendukungnya (termasuk llama3.2) — setiap tool punya name
# (harus PERSIS sama dengan key di TOOL_FUNCTIONS di bawah), description
# (penjelasan buat LLM, bukan buat manusia — tulis sejelas mungkin supaya LLM
# tidak salah pilih tool), dan parameters (aturan argumen yang dibutuhkan,
# ditulis dalam format JSON Schema).
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "WAJIB dipanggil setiap kali user menanyakan soal cuaca, suhu, "
                "atau kondisi langit — dengan cara apapun user bertanya, "
                "termasuk kalau user tidak menyebutkan kota spesifik. Jangan "
                "pernah menjawab pertanyaan cuaca tanpa memanggil tool ini."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": (
                            "Nama kota, contoh: Jakarta, Bandung, Surabaya. "
                            "Kosongkan string ini kalau user tidak menyebutkan "
                            "kota spesifik (misal cuma bilang 'cuaca hari ini')."
                        ),
                    }
                },
                # CATATAN: "location" SENGAJA tidak dimasukkan ke "required" —
                # kita mau LLM tetap bisa manggil tool ini walau user nggak
                # sebut kota, karena weather_tool.py sudah punya fallback ke
                # DEFAULT_LOCATION kalau location dikirim kosong.
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "play_song",
            "description": "Memutar sebuah lagu tertentu di Spotify.",
            "parameters": {
                "type": "object",
                "properties": {
                    "song_name": {
                        "type": "string",
                        "description": "Judul lagu yang ingin diputar, boleh disertai nama artis untuk hasil lebih akurat.",
                    }
                },
                "required": ["song_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pause_music",
            "description": "Menjeda musik yang sedang diputar di Spotify.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resume_music",
            "description": "Melanjutkan musik yang sebelumnya dijeda di Spotify.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

# Dictionary penghubung: key = nama tool (harus PERSIS sama dengan "name" di
# TOOLS_SCHEMA di atas), value = fungsi Python yang benar-benar dipanggil.
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "play_song": play_song,
    "pause_music": pause_music,
    "resume_music": resume_music,
}