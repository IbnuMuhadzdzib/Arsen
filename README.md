# Arsen Assistant — Setup Guide

Panduan ini mengasumsikan kamu belum pernah setup project Python dari nol,
jadi tiap command dijelaskan: **di folder mana dijalankan**, **apa fungsinya**,
dan **kenapa** langkahnya seperti itu.

## Struktur Folder Project

Setelah semua langkah selesai, struktur foldernya akan seperti ini:

```
arsen-assistant/              <- folder utama project (folder ini)
├── requirements.txt          <- daftar library yang dibutuhkan
├── config.py                 <- semua pengaturan (path, nama model, dll)
├── vad_helper.py              <- deteksi kapan kamu selesai bicara
├── wake_word_listener.py     <- deteksi "Hey Arsen"
├── stt_engine.py             <- ubah suara jadi teks
├── llm_client.py             <- kirim pertanyaan ke LLM
├── tts_engine.py              <- ubah teks jadi suara
├── main.py                    <- file yang kamu jalankan untuk menyalakan Arsen
├── README.md                  <- file ini
├── models/                    <- KAMU buat folder ini, isi model yang didownload manual
│   ├── hey_jarwis_v0.1.tflite  (contoh nama, sesuaikan dengan yang didownload)
│   └── id_ID-voice-medium.onnx (contoh nama, sesuaikan dengan yang didownload)
└── arsen-env/                 <- dibuat otomatis saat setup, ISI virtual environment
```

Semua file `.py` di atas sudah gw buatkan — yang perlu kamu lakukan cuma
langkah-langkah setup di bawah ini.

---

## Langkah 1 — Pastikan Semua File Ada di Satu Folder

Download semua file (`requirements.txt`, `config.py`, `vad_helper.py`, dst)
dan taruh dalam **satu folder yang sama**, misal `arsen-assistant/` di folder
Documents kamu. Semua command di bawah harus dijalankan **dari dalam folder
ini** — kalau kamu jalankan dari folder lain, Python tidak akan menemukan
file-file yang saling terhubung (misal `main.py` butuh `config.py` di folder
yang sama persis).

Buka Terminal (Mac/Linux) atau Command Prompt/PowerShell (Windows), lalu:

```bash
cd ~/Documents/arsen-assistant
```

**Penjelasan syntax:**
- `cd` = *change directory*, perintah untuk berpindah folder aktif di terminal
- `~` = shortcut untuk folder home user kamu (misal `/Users/nama-kamu` di Mac)
- Setelah command ini, semua command berikutnya "berdiri" di folder ini

---

## Langkah 2 — Buat Virtual Environment

Masih di folder `arsen-assistant/`, jalankan:

```bash
python -m venv arsen-env
```

**Penjelasan syntax:**
- `python` = memanggil interpreter Python
- `-m venv` = `-m` artinya "jalankan module bernama venv sebagai program utama";
  `venv` adalah module bawaan Python untuk membuat virtual environment
- `arsen-env` = nama folder yang akan dibuat untuk menyimpan environment ini
  (kamu bisa kasih nama lain, tapi di panduan ini kita konsisten pakai nama ini)

**Kenapa langkah ini penting:** virtual environment adalah "kotak terpisah"
berisi Python dan semua library khusus untuk project ini — supaya tidak
bentrok dengan Python sistem kamu atau project lain.

Aktifkan environment yang baru dibuat:

```bash
# Mac / Linux:
source arsen-env/bin/activate

# Windows (Command Prompt):
arsen-env\Scripts\activate.bat

# Windows (PowerShell):
arsen-env\Scripts\Activate.ps1
```

**Penjelasan syntax:**
- `source` (Mac/Linux) = menjalankan script `activate` di dalam sesi terminal
  yang sedang berjalan sekarang (bukan sesi baru), supaya perubahan environment
  variable-nya benar-benar berlaku
- Setelah dijalankan, kamu akan lihat `(arsen-env)` muncul di awal baris
  terminal kamu — ini tanda environment sudah aktif

**Penting:** setiap kali kamu buka terminal baru untuk kerja di project ini
lagi nanti, kamu harus jalankan ulang command `activate` ini (tidak permanen
per sesi terminal).

---

## Langkah 3 — Install Semua Library

Pastikan `(arsen-env)` masih muncul di terminal kamu (environment aktif), lalu:

```bash
pip install -r requirements.txt
```

**Penjelasan syntax:**
- `pip` = package installer untuk Python
- `install -r requirements.txt` = install semua package yang terdaftar di
  file `requirements.txt` (lihat isi file itu untuk penjelasan tiap library)

Proses ini bisa memakan waktu beberapa menit tergantung koneksi internet,
karena beberapa library (terutama `torch`) ukurannya cukup besar.

---

## Langkah 4 — Install & Setup Ollama (LLM Lokal)

Ollama **bukan** library Python biasa (tidak lewat pip) — ini aplikasi
terpisah yang jalan sebagai server di background.

1. Download installer dari [ollama.com](https://ollama.com) sesuai OS kamu, install seperti aplikasi biasa
2. Buka terminal (boleh terminal baru, di luar folder project, karena ini
   perintah global bukan bagian dari project files), jalankan:

```bash
ollama pull llama3.2:3b
```

**Penjelasan syntax:**
- `ollama pull` = download model AI dari Ollama library ke komputer kamu
- `llama3.2:3b` = nama model (`llama3.2`) dan ukurannya (`3b` = 3 miliar
  parameter) — ukuran ini dipilih supaya cukup cepat jalan di CPU laptop kamu

Ollama otomatis jalan sebagai server begitu terinstall — kamu bisa cek dengan:

```bash
ollama run llama3.2:3b "test"
```

Kalau muncul jawaban teks, artinya Ollama sudah siap dan `llm_client.py`
nanti bisa langsung connect ke server-nya di `localhost:11434`.

---

## Langkah 5 — Download Model Wake Word & TTS

Dua model ini adalah file binary (bukan kode), jadi harus didownload manual
dari sumbernya:

1. **Model wake word** (openWakeWord): download model bawaan (misal
   `hey_jarvis_v0.1.tflite`) dari repository resmi openWakeWord di GitHub —
   pakai ini dulu sebagai placeholder untuk testing pipeline, sebelum kamu
   training wake word custom "Hey Arsen" di tahap berikutnya
2. **Model suara Piper** (format `.onnx` + file `.onnx.json` pasangannya):
   download voice model Bahasa Indonesia dari halaman voices resmi Piper —
   kalau opsi Bahasa Indonesia kurang natural saat dites, pakai voice Bahasa
   Inggris dulu untuk validasi pipeline, baru cari alternatif TTS lain
   khusus kualitas suara nanti

Buat folder `models/` di dalam `arsen-assistant/`, taruh kedua file model itu
(untuk Piper, dua file: `.onnx` dan `.onnx.json`-nya harus satu folder yang
sama):

```bash
mkdir models
```

Lalu sesuaikan nama file di `config.py` (baris `WAKE_WORD_MODEL_PATH` dan
`TTS_VOICE_MODEL_PATH`) supaya cocok dengan nama file yang benar-benar kamu
download — nama file bisa beda tergantung versi yang kamu ambil.

3. **Piper executable (piper.exe)**: karena package Python `piper-tts` tidak
   kompatibel dengan Python 3.14 kamu (lihat penjelasan error sebelumnya),
   kita pakai Piper versi standalone. Download rilisan Windows
   (`piper_windows_amd64.zip` atau nama serupa) dari halaman **Releases** di
   repository GitHub resmi Piper (`rhasspy/piper`), lalu extract seluruh isi
   zip itu (termasuk `piper.exe` dan file-file `.dll` pendampingnya — jangan
   dipisah, semua file dalam satu zip itu saling dibutuhkan) ke folder baru:

```bash
mkdir piper
```

   Pastikan hasil extract-nya membuat `piper.exe` ada persis di
   `arsen-assistant/piper/piper.exe` — sesuai path yang sudah diset di
   `config.py` (`PIPER_EXE_PATH`). Kalau kamu extract ke lokasi/struktur
   folder lain, sesuaikan juga path-nya di `config.py`.

---

## Langkah 6 — Jalankan Arsen

Pastikan:
- Environment masih aktif (`(arsen-env)` muncul di terminal)
- Kamu masih di dalam folder `arsen-assistant/`
- Ollama sudah jalan (dari Langkah 4)
- File model sudah ada di folder `models/` (dari Langkah 5)

```bash
python main.py
```

Kalau semua berjalan lancar, terminal akan menampilkan:
```
Arsen siap. Menunggu wake word...
```

Ucapkan wake word (sesuai model yang kamu pakai), dan Arsen akan mulai
merekam, memproses, lalu menjawab dengan suara.

---

## Troubleshooting Umum

- **`ModuleNotFoundError`**: biasanya artinya environment belum aktif, atau
  `pip install -r requirements.txt` belum selesai/gagal di tengah jalan —
  cek ulang Langkah 2 dan 3
- **Tidak ada suara/mic tidak terdeteksi**: cek permission mikrofon di
  pengaturan sistem OS kamu — banyak OS modern minta izin eksplisit untuk
  aplikasi/terminal mengakses mikrofon
- **Respons sangat lambat**: normal di percobaan pertama (model perlu
  "pemanasan"). Kalau tetap lambat terus-menerus, ukur tiap komponen secara
  terpisah (tambahkan `print` dengan `time.time()` sebelum-sesudah tiap
  langkah di `main.py`) untuk cari komponen mana yang jadi bottleneck

---

## Fase 2 — Setup Function Calling (Cuaca & Musik)

Dua tool baru ini butuh API key/credential eksternal — keduanya gratis,
tapi Spotify butuh langkah setup lebih panjang karena pakai OAuth.

### Setup OpenWeatherMap (Cuaca)

1. Daftar akun gratis di [openweathermap.org/api](https://openweathermap.org/api)
2. Setelah daftar, masuk ke halaman **API keys** di akun kamu, copy API key
   yang otomatis dibuatkan (atau generate baru)
3. Tempel API key itu ke `config.py`, baris `OPENWEATHER_API_KEY`
4. **Catatan**: API key baru biasanya butuh waktu beberapa menit sampai
   1-2 jam sebelum aktif — kalau langsung dites error "invalid API key",
   tunggu sebentar dan coba lagi
5. Edit juga `DEFAULT_LOCATION` di `config.py` ke kota kamu sendiri (format:
   `"NamaKota,ID"`)

### Setup Spotify (Kontrol Musik)

**Prasyarat: akun Spotify kamu harus Premium** — API kontrol playback tidak
bisa dipakai akun Free.

1. Buka [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard), login pakai akun Spotify kamu
2. Klik **Create app**, isi nama & deskripsi bebas
3. Di bagian **Redirect URIs**, tambahkan persis:
   ```
   http://127.0.0.1:8888/callback
   ```
   (harus sama persis dengan `SPOTIFY_REDIRECT_URI` di `config.py` — Spotify
   menolak request kalau tidak cocok)
4. Save, lalu buka halaman app yang baru dibuat, klik **Settings** untuk
   lihat **Client ID** dan **Client Secret**
5. Tempel keduanya ke `config.py` (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`)

**Login pertama kali (sekali saja):**

Saat pertama kali fitur musik dipanggil (misal kamu bilang "putar lagu..."),
browser akan otomatis terbuka minta kamu login Spotify dan klik **Agree**
untuk kasih izin. Setelah itu, token disimpan otomatis di file `.cache` di
folder project — run berikutnya tidak perlu login ulang.

**Sebelum coba kontrol musik**, pastikan:
- Aplikasi Spotify (HP/laptop/speaker manapun) sedang terbuka — walau tidak
  sedang muter apapun, minimal app-nya harus "aktif" supaya Spotify tau mau
  kirim perintah ke device mana

