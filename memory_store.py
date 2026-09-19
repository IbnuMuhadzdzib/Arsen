"""
memory_store.py — Menyimpan histori percakapan Arsen secara PERMANEN pakai
SQLite, supaya obrolan nggak hilang total tiap kali program di-restart.

KENAPA SQLite (bukan file .txt biasa)?
SQLite adalah database beneran (punya tabel, bisa di-query pakai SQL) tapi
wujudnya cuma SATU FILE di komputer kamu — nggak perlu install/jalanin
server database terpisah. `sqlite3` juga sudah termasuk bawaan Python
(`import sqlite3` langsung bisa dipakai), jadi nggak nambah dependency baru
di requirements.txt.
"""

import sqlite3
from config import BASE_DIR
import os

# Database disimpan sebagai satu file di folder project, sejajar sama main.py
DB_PATH = os.path.join(BASE_DIR, "arsen_memory.db")


def _get_connection() -> sqlite3.Connection:
    """
    sqlite3.connect() membuka koneksi ke file database itu — kalau filenya
    belum ada sama sekali, SQLite OTOMATIS membuatnya. Nggak ada langkah
    "buat database dulu" terpisah kayak database server pada umumnya.
    """
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """
    Membuat tabel 'messages' kalau belum ada. Dipanggil sekali di awal
    (saat llm_client.py di-import), aman dipanggil berkali-kali tiap run
    karena pakai "IF NOT EXISTS".
    """
    conn = _get_connection()
    cursor = conn.cursor()

    # Struktur tabel:
    # - id: nomor urut otomatis, jadi identitas unik tiap baris
    # - role: "user" atau "assistant", siapa yang "ngomong"
    # - content: isi pesannya
    # - timestamp: kapan pesan ini disimpan, otomatis diisi SQLite sendiri
    #   (CURRENT_TIMESTAMP) tanpa kita perlu generate manual dari Python
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()  # commit = "simpan beneran" perubahan ke file database
    conn.close()


def save_message(role: str, content: str) -> None:
    """
    Simpan satu pesan ke database.

    Parameter:
    - role: "user" atau "assistant"
    - content: isi pesan

    Catatan keamanan: pakai tanda tanya (?) sebagai placeholder untuk value,
    BUKAN menggabung string manual (misal f"...{content}..."). Ini teknik
    standar untuk mencegah SQL injection — walau di project personal kayak
    gini risikonya kecil, ini kebiasaan yang penting dibawa terus.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (role, content) VALUES (?, ?)",
        (role, content),
    )
    conn.commit()
    conn.close()


def load_recent_messages(limit: int = 10) -> list[dict]:
    """
    Ambil N pesan TERAKHIR dari database, dipakai untuk "prime" (isi awal)
    conversation_history saat program baru nyala.

    Kenapa cuma N pesan terakhir, bukan SEMUA histori sejak awal?
    LLM punya batas "context window" (berapa banyak teks yang bisa dibaca
    sekaligus dalam satu request) — kalau kita kirim SELURUH histori dari
    bulan lalu setiap kali chat, itu akan (1) akhirnya melebihi batas
    tersebut, dan (2) bikin tiap respons makin lambat makin lama Arsen
    dipakai (karena LLM harus "membaca" teks yang makin panjang). 10 pesan
    terakhir cukup untuk konteks nyambung tanpa bikin berat.

    Return: list of dict dengan format {"role": ..., "content": ...} — format
    ini sama persis dengan yang dipakai conversation_history di llm_client.py,
    jadi bisa langsung digabung tanpa perlu konversi.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    # ORDER BY id DESC = urutkan dari ID PALING BESAR dulu (= paling baru).
    # LIMIT ? = ambil cuma `limit` baris teratas dari urutan itu.
    cursor.execute(
        "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()

    # rows sekarang urutannya TERBALIK (paling baru di depan) karena DESC
    # di atas — kita balik lagi jadi urutan kronologis (lama ke baru) pakai
    # [::-1], karena itu urutan yang benar untuk sebuah "riwayat obrolan"
    rows = rows[::-1]

    return [{"role": role, "content": content} for role, content in rows]
