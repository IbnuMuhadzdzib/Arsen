"""
wake_word_listener.py — Mendengarkan mikrofon terus-menerus di background,
menunggu wake word terucap ("Hey Arsen" / placeholder "Hey Jarvis" untuk testing awal).

KENAPA INI JALAN TERUS TAPI TETAP RINGAN?
Model wake word ukurannya kecil banget (beda jauh dari model STT/LLM), jadi
aman dijalankan nonstop tanpa bikin laptop berat — inilah alasan wake word
detection dipisah dari STT (lihat penjelasan di panduan sebelumnya).
"""

import numpy as np
import sounddevice as sd
from openwakeword.model import Model
from config import WAKE_WORD_MODEL_PATH, WAKE_WORD_THRESHOLD, SAMPLE_RATE, CHANNELS

# Model(...) memuat file model wake word yang sudah didownload ke folder models/.
# wakeword_models menerima LIST karena openWakeWord bisa mendengarkan beberapa
# wake word sekaligus — di sini kita cuma pakai satu.
oww_model = Model(wakeword_models=[WAKE_WORD_MODEL_PATH])


def listen_for_wake_word() -> bool:
    """
    Fungsi ini BLOCKING — artinya kode di baris setelah pemanggilan fungsi ini
    tidak akan jalan sampai wake word benar-benar terdeteksi. Ini disengaja,
    karena di state IDLE, program memang tidak punya kerjaan lain selain
    menunggu wake word.

    Return: True begitu wake word terdeteksi (fungsi ini tidak pernah return False,
    dia cuma "selesai" ketika True).
    """
    frame_length = 1280  # openWakeWord butuh potongan audio 80ms per prediksi
                          # (1280 sample / 16000 Hz = 0.08 detik) — angka ini
                          # sudah ditentukan oleh cara model ini dilatih, bukan angka bebas.

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16") as stream:
        while True:
            # Ambil satu potongan kecil audio dari mikrofon
            audio_frame, _ = stream.read(frame_length)
            audio_frame = audio_frame.flatten().astype(np.int16)

            # .predict() mengembalikan dictionary, contoh:
            # {"hey_jarwis": 0.02, "hey_jarwis_v2": 0.87, ...}
            # Key-nya nama model, value-nya skor kemiripan (0.0 - 1.0)
            prediction = oww_model.predict(audio_frame)

            # .values() mengambil semua skor dari dictionary itu, max() ambil yang tertinggi
            highest_score = max(prediction.values())

            if highest_score > WAKE_WORD_THRESHOLD:
                return True
