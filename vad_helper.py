"""
vad_helper.py — Voice Activity Detection.

TUGAS FILE INI: merekam suara dari mikrofon, dan otomatis BERHENTI merekam
begitu mendeteksi kamu sudah diam (bukan berdasarkan timer tetap, tapi
berdasarkan benar-benar mendengarkan ada suara atau tidak).
"""

import torch
import numpy as np
import sounddevice as sd
from config import SAMPLE_RATE, CHANNELS

# torch.hub.load mendownload (sekali saja, lalu di-cache) dan memuat model
# Silero VAD langsung dari repository GitHub resminya.
# repo_or_dir = lokasi sumber model, model= nama model yang mau diambil dari repo itu.
model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
)
# utils berisi beberapa fungsi bantuan bawaan dari Silero — kita ambil satu yang
# kita butuh, yaitu get_speech_timestamps (mencari kapan ada suara di dalam audio).
(get_speech_timestamps, _, _, _, _) = utils


def record_until_silence(max_seconds: int = 15, silence_limit: float = 1.0) -> np.ndarray:
    """
    Merekam audio dari mikrofon sampai user diam selama `silence_limit` detik,
    atau sampai `max_seconds` tercapai (safety limit biar nggak rekam selamanya
    kalau VAD gagal mendeteksi keheningan karena ada noise background).

    Parameter:
    - max_seconds: batas maksimal rekaman (detik) — jaga-jaga/safety net.
    - silence_limit: berapa lama diam (detik) sebelum dianggap "user selesai bicara".

    Return: audio dalam bentuk numpy array (angka-angka amplitudo suara),
    supaya bisa langsung dipakai komponen lain (STT) tanpa nulis ke file dulu.
    """
    # Silero VAD versi ini MENGHARUSKAN input persis 512 sample per panggilan
    # (untuk sample rate 16000 Hz) — bukan ukuran bebas. 512 sample / 16000 Hz
    # = 0.032 detik per potongan, jauh lebih kecil dari sebelumnya (dulu 0.5 detik,
    # itu yang menyebabkan error "Provided number of samples is 8000").
    chunk_samples = 512
    chunk_duration = chunk_samples / SAMPLE_RATE  # ~0.032 detik

    audio_chunks = []       # tempat menyimpan semua potongan audio yang direkam
    silence_duration = 0.0  # penghitung berapa lama sudah diam berturut-turut
    total_duration = 0.0
    speech_started = False  # PENTING: penanda apakah suara user sudah pernah
                             # terdeteksi sejak rekaman ini dimulai. Tanpa flag ini,
                             # jeda natural sepersekian detik SEBELUM user mulai
                             # bicara (misal jeda antara selesai bilang wake word
                             # dan mulai kalimat berikutnya) akan dihitung sebagai
                             # "sudah selesai bicara", sehingga rekaman berhenti
                             # sebelum user sempat ngomong sama sekali.

    # sd.InputStream membuka koneksi streaming ke mikrofon — beda dengan
    # sd.rec() biasa yang merekam durasi tetap, InputStream bisa kita baca
    # sedikit-sedikit secara real-time sambil kita putuskan kapan berhenti.
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32") as stream:
        while total_duration < max_seconds:
            # stream.read() mengambil potongan audio terbaru dari mikrofon.
            # Return-nya tuple (data, overflowed) — kita cuma butuh data-nya.
            chunk, _ = stream.read(chunk_samples)
            chunk = chunk.flatten()  # ubah dari bentuk 2D (samples, channels) jadi 1D
            audio_chunks.append(chunk)
            total_duration += chunk_duration

            # Konversi potongan audio ke format tensor yang dimengerti Silero VAD
            chunk_tensor = torch.from_numpy(chunk)

            # model(...) di sini adalah cara memanggil Silero VAD untuk satu
            # potongan audio — hasilnya skor 0.0-1.0, makin tinggi makin
            # kemungkinan ada suara manusia di potongan itu.
            speech_prob = model(chunk_tensor, SAMPLE_RATE).item()

            if speech_prob >= 0.4:
                # Ada suara terdeteksi → tandai bahwa user sudah mulai bicara,
                # dan reset penghitung diam ke 0
                speech_started = True
                silence_duration = 0.0
            elif speech_started:
                # Skor rendah = kemungkinan besar ini keheningan/noise.
                # TAPI cuma dihitung kalau user SUDAH PERNAH kedeteksi bicara —
                # supaya diam di awal (sebelum user mulai ngomong) tidak
                # dianggap sebagai "user sudah selesai bicara".
                silence_duration += chunk_duration

            if speech_started and silence_duration >= silence_limit:
                # User sudah bicara, DAN sudah diam cukup lama setelahnya
                # → anggap user selesai bicara, hentikan loop
                break

    # np.concatenate menggabungkan semua potongan kecil jadi satu array audio utuh
    return np.concatenate(audio_chunks)