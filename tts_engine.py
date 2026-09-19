"""
tts_engine.py — Text-to-Speech menggunakan Piper.

TUGAS FILE INI: terima teks jawaban dari LLM, keluarkan audio yang bisa diputar.

KENAPA PAKAI subprocess KE piper.exe, BUKAN package Python `piper-tts`?
Package Python-nya bergantung ke `piper-phonemize` (extension C++) yang belum
punya rilisan untuk Python 3.14. Piper juga menyediakan versi standalone
(.exe) yang berdiri sendiri sebagai program — dengan memanggilnya lewat
subprocess, kita tidak bergantung sama sekali ke kompatibilitas package
Python untuk fitur TTS ini.
"""

import subprocess
import tempfile
import os
import wave
import numpy as np
import sounddevice as sd
from config import PIPER_EXE_PATH, TTS_VOICE_MODEL_PATH


def speak(text: str) -> None:
    """
    Parameter:
    - text: jawaban dari llm_client.ask_llm()

    Fungsi ini tidak return apa-apa (None) — tugasnya langsung memutar audio
    ke speaker, bukan mengembalikan data untuk diproses lebih lanjut.
    """
    # tempfile.NamedTemporaryFile membuat file kosong sementara di folder temp
    # sistem, dengan nama unik otomatis — dipakai sebagai lokasi piper.exe
    # menyimpan hasil audio-nya. delete=False supaya file tidak langsung
    # terhapus begitu blok `with` selesai (kita masih butuh baca isinya setelah ini).
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        output_path = tmp_file.name

    try:
        # subprocess.run menjalankan piper.exe seolah-olah kamu ngetik command ini
        # sendiri di terminal:
        #   piper.exe --model <path_model> --output_file <path_output>
        #
        # input=text.encode("utf-8") mengirim teks ke piper.exe lewat stdin.
        # check=True membuat Python otomatis melempar error kalau piper.exe gagal.
        subprocess.run(
            [PIPER_EXE_PATH, "--model", TTS_VOICE_MODEL_PATH, "--output_file", output_path],
            input=text.encode("utf-8"),
            check=True,
        )

        # wave.open membaca file .wav yang barusan dibuat piper.exe.
        with wave.open(output_path, "rb") as wf:
            frames = wf.readframes(wf.getnframes())      # ambil semua sample audio
            audio_array = np.frombuffer(frames, dtype=np.int16)  # ubah jadi array angka
            actual_sample_rate = wf.getframerate()        # ambil sample rate ASLI dari file wav

        # Putar audio ke speaker, lalu tunggu sampai selesai
        sd.play(audio_array, samplerate=actual_sample_rate)
        sd.wait()

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Piper TTS gagal: {e}")
    except Exception as e:
        print(f"[ERROR] Gagal memutar audio: {e}")
    finally:
        # Hapus file sementara — SELALU dijalankan, bahkan kalau ada error di atas.
        # Tanpa finally, file .wav akan menumpuk di folder temp kalau piper crash.
        if os.path.exists(output_path):
            os.remove(output_path)
