"""
main.py — Titik masuk utama program. Ini file yang kamu jalankan
(`python main.py`) untuk menyalakan Arsen.

Menjalankan state machine: IDLE -> RECORDING -> PROCESSING -> SPEAKING -> IDLE
(lihat penjelasan state machine di panduan sebelumnya).
"""

# --- Suppress noisy warnings dari dependencies ---
# Harus di atas SEMUA import supaya filter aktif sebelum module lain loaded.
import warnings
import logging
import os

# 1. tflite runtime warning dari openwakeword (nggak bahaya, dia fallback ke onnx)
# 2. torch.jit.load FutureWarning dari Silero VAD (deprecation, belum ada efeknya)
warnings.filterwarnings("ignore", message=".*tflite.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

# 3. HuggingFace Hub "unauthenticated requests" warning (cuma muncul pas download model)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

# 4. Root logger warning dari openwakeword tflite fallback
logging.getLogger().setLevel(logging.ERROR)

# 5. Suppress ONNX Runtime warnings yang kadang muncul
os.environ["ORT_LOG_LEVEL"] = "3"  # ERROR only

from wake_word_listener import listen_for_wake_word
from vad_helper import record_until_silence
from stt_engine import transcribe
from llm_client import ask_llm
from tts_engine import speak
from config import SAMPLE_RATE


def main():
    print("Arsen siap. Menunggu wake word...")

    while True:
        # --- STATE: IDLE ---
        # Baris ini BLOCKING (program berhenti di sini) sampai wake word terdeteksi.
        listen_for_wake_word()
        print("Wake word terdeteksi! Mendengarkan...")

        try:
            # --- STATE: RECORDING ---
            # Merekam sampai kamu diam (bukan durasi tetap) — lihat vad_helper.py
            audio = record_until_silence()

            # --- STATE: PROCESSING ---
            print("Memproses...")

            # 1. Audio -> Teks
            user_text = transcribe(audio, sample_rate=SAMPLE_RATE)
            print(f"Kamu bilang: {user_text}")

            # Kalau hasil transkripsi kosong (misal cuma noise, bukan suara jelas),
            # skip proses LLM & TTS, langsung kembali dengarkan wake word lagi.
            if not user_text.strip():
                print("Tidak ada ucapan terdeteksi, kembali menunggu wake word.")
                continue

            # --- CEK VOICE COMMAND BAWAAN ---
            # Kita tangkap string ini sebelum dikirim ke LLM
            lower_text = user_text.lower()
            if any(cmd in lower_text for cmd in ["shutdown", "matikan arsen", "berhenti", "matikan program", "matikan sistem"]):
                print("Shutdown command terdeteksi.")
                speak("Baik. Arsen telah dimatikan. Sampai jumpa!")
                break

            # 2. Teks -> Jawaban LLM
            reply_text = ask_llm(user_text)
            print(f"Arsen: {reply_text}")

            # --- STATE: SPEAKING ---
            # 3. Jawaban -> Suara
            speak(reply_text)

        except KeyboardInterrupt:
            # Ctrl+C = user sengaja matikan program, biarkan keluar
            print("\nArsen dimatikan. Sampai jumpa!")
            break
        except Exception as e:
            # Error lain (Ollama mati, Piper crash, mic error, dll) —
            # JANGAN crash seluruh program. Log error, lalu kembali ke
            # state IDLE untuk menunggu wake word lagi.
            print(f"[ERROR] Terjadi kesalahan: {e}")
            print("Kembali menunggu wake word...")
            continue


if __name__ == "__main__":
    main()

