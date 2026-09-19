"""
music_tool.py — Kontrol playback Spotify (play, pause, resume).

SYARAT PENTING (bukan salah kode kalau ini nggak terpenuhi):
1. Akun Spotify kamu harus PREMIUM — kontrol playback lewat API cuma
   diizinkan Spotify untuk akun Premium, akun Free tidak bisa.
2. Harus ada MINIMAL SATU device Spotify yang aktif — buka app Spotify (HP,
   laptop, atau speaker manapun) dan pastikan sedang "nyala" (nggak harus
   sedang muter lagu, yang penting app-nya kebuka), supaya Spotify tau mau
   ngirim perintah play ke device mana.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPE,
)

# Variabel global ini SENGAJA diawali None (belum langsung connect ke Spotify).
# Kenapa: kalau kita connect di sini (level module, langsung pas file di-import),
# maka SELURUH PROGRAM gagal jalan kalau Spotify belum dikonfigurasi — padahal
# fitur lain (cuaca, dll) sama sekali nggak butuh Spotify. Dengan pola "lazy
# initialization" ini, koneksi ke Spotify baru benar-benar dibuat saat salah
# satu fungsi musik di file ini PERTAMA KALI dipanggil.
sp = None


def _get_spotify_client():
    """
    Fungsi internal (diawali underscore, konvensi Python untuk "jangan dipanggil
    dari file lain") yang memastikan client Spotify sudah siap sebelum dipakai.
    """
    global sp

    if sp is not None:
        # Sudah pernah di-setup sebelumnya (dari pemanggilan fungsi musik
        # sebelumnya) → pakai yang sudah ada, tidak perlu setup ulang.
        return sp

    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        # Kasih pesan error yang JELAS actionable, bukan traceback teknis
        # yang membingungkan — kita tau persis apa yang kurang.
        raise RuntimeError(
            "SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET belum diisi di config.py. "
            "Lihat README.md bagian 'Setup Spotify' untuk cara mendapatkannya."
        )

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE,
    ))
    return sp


def play_song(song_name: str) -> str:
    """
    Parameter:
    - song_name: judul lagu yang mau diputar, boleh disertai nama artis
      untuk hasil pencarian yang lebih akurat (misal "Bohemian Rhapsody Queen")

    Return: string konfirmasi untuk LLM, apa yang berhasil/gagal dilakukan.
    """
    # sp.search() mencari lagu di seluruh katalog Spotify berdasarkan teks.
    # type="track" = cari lagu (bukan album/artis/playlist).
    # limit=1 = ambil HASIL PALING RELEVAN SATU AJA — untuk voice assistant,
    # kita nggak mau nanya balik "maksud kamu yang mana dari 10 hasil ini?",
    # langsung ambil tebakan terbaik Spotify.
    try:
        client = _get_spotify_client()
    except RuntimeError as e:
        return str(e)

    results = client.search(q=song_name, type="track", limit=1)
    tracks = results["tracks"]["items"]

    if not tracks:
        return f"Lagu '{song_name}' tidak ditemukan di Spotify."

    track = tracks[0]
    track_uri = track["uri"]           # ID unik lagu ini di Spotify, dibutuhkan buat play
    track_title = track["name"]
    artist_name = track["artists"][0]["name"]

    try:
        # start_playback dengan parameter uris=[...] artinya "putar lagu spesifik
        # ini", bukan cuma resume lagu yang lagi paused sebelumnya
        client.start_playback(uris=[track_uri])
    except spotipy.exceptions.SpotifyException:
        # Exception ini paling sering muncul kalau tidak ada device aktif,
        # atau akunnya bukan Premium — pesan errornya dibuat actionable,
        # kasih tau user harus ngapain, bukan cuma "terjadi error"
        return (
            "Tidak bisa memutar lagu — pastikan Spotify sedang terbuka di salah "
            "satu device kamu dan akun Spotify kamu Premium."
        )

    return f"Memutar '{track_title}' oleh {artist_name}."


def pause_music() -> str:
    """Tidak butuh parameter — LLM akan memanggil ini tanpa argumen apapun."""
    try:
        client = _get_spotify_client()
        client.pause_playback()
        return "Musik dijeda."
    except RuntimeError as e:
        return str(e)
    except spotipy.exceptions.SpotifyException:
        return "Tidak ada musik yang sedang diputar untuk dijeda."


def resume_music() -> str:
    """Melanjutkan lagu yang sebelumnya dijeda (bukan memutar lagu baru)."""
    try:
        client = _get_spotify_client()
        client.start_playback()  # tanpa parameter uris= → melanjutkan dari posisi terakhir
        return "Musik dilanjutkan."
    except RuntimeError as e:
        return str(e)
    except spotipy.exceptions.SpotifyException:
        return "Tidak ada musik yang bisa dilanjutkan."