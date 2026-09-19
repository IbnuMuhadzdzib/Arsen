"""
stt_engine.py — Speech-to-Text menggunakan faster-whisper.

TUGAS FILE INI: terima audio (angka-angka dari mikrofon), keluarkan teks.
"""

from faster_whisper import WhisperModel
import numpy as np

# WhisperModel(...) memuat model ke memory SEKALI SAJA saat file ini di-import
# (bukan setiap kali fungsi dipanggil) — supaya loading model yang agak berat
# nggak diulang tiap ada request, cukup sekali di awal program jalan.
#
# "medium"      = ukuran model yang lebih akurat dari "small", terutama untuk
#                 Bahasa Indonesia dan kalimat pendek informal. Trade-off:
#                 loading awal lebih lama (~10 detik), tapi inference tetap OK.
# device="cpu"  = eksplisit bilang pakai CPU (bukan GPU).
# compute_type="int8" = kuantisasi 8-bit — mempercepat proses di CPU.
stt_model = WhisperModel("medium", device="cpu", compute_type="int8")

# Prompt awal berisi contoh percakapan Bahasa Indonesia informal — ini memberi
# konteks ke Whisper supaya bias decoding-nya ke bahasa Indonesia casual/slang,
# bukan bahasa formal/berita. Ini BUKAN instruksi, tapi "contoh teks sebelumnya"
# yang mempengaruhi probabilitas kata-kata berikutnya.
INITIAL_PROMPT = (
    "Halo, apa kabar? Gue lagi gabut nih, lo lagi ngapain? "
    "Eh kemarin gue nonton film bagus banget sih. "
    "Makasih ya, nanti gue kabarin lagi."
)


def transcribe(audio: np.ndarray, sample_rate: int = 16000) -> str:
    """
    Parameter:
    - audio: array angka hasil rekaman (dari vad_helper.record_until_silence())
    - sample_rate: harus sama dengan yang dipakai saat merekam (16000 Hz)

    Return: teks hasil transkripsi, dalam bentuk string biasa.
    """
    # language="id"    = paksa Bahasa Indonesia (skip auto-detect).
    # beam_size=5      = evaluasi 5 jalur decoding alternatif, bukan cuma 1
    #                    (greedy). Jauh lebih akurat untuk kalimat pendek.
    # vad_filter=True  = filter VAD bawaan Whisper — buang segmen silence/noise,
    #                    mengurangi hallucination (Whisper sering "mengarang" teks
    #                    dari keheningan kalau filter ini mati).
    # initial_prompt   = konteks bahasa informal supaya Whisper nggak bias ke
    #                    bahasa formal/berita.
    segments, info = stt_model.transcribe(
        audio,
        language="id",
        beam_size=5,
        vad_filter=True,
        initial_prompt=INITIAL_PROMPT,
    )

    # Gabungkan semua segmen jadi satu string.
    full_text = " ".join(segment.text.strip() for segment in segments)

    return full_text
