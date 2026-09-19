"""
weather_tool.py — Mengambil data cuaca real dari OpenWeatherMap API.

Ini salah satu "tool" yang didaftarkan ke LLM lewat schema.py — LLM akan
memanggil fungsi get_weather() di file ini kalau dia mendeteksi user
menanyakan soal cuaca.
"""

import requests
from config import OPENWEATHER_API_KEY, DEFAULT_LOCATION


def get_weather(location: str = "") -> str:
    """
    Parameter:
    - location: nama kota, misal "Jakarta" atau "Jakarta,ID". Boleh dikosongkan
      (default "") — kalau kosong, dianggap user tidak menyebutkan kota
      spesifik, jadi kita pakai DEFAULT_LOCATION dari config.py.

    Return: string deskripsi cuaca dalam Bahasa Indonesia. String ini nanti
    dikirim balik ke LLM (bukan langsung ke user), supaya LLM yang merangkai
    jadi kalimat natural — bukan dibacakan mentah-mentah apa adanya.
    """
    # Kalau LLM tidak memberikan location (string kosong), pakai default
    if not location.strip():
        location = DEFAULT_LOCATION

    url = "https://api.openweathermap.org/data/2.5/weather"

    # Parameter query untuk API OpenWeatherMap:
    params = {
        "q": location,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",  # metric = hasil suhu dalam Celsius. Tanpa ini,
                             # API defaultnya balikin Kelvin (misal 300K,
                             # bukan 27°C) — jelas nggak natural buat dibaca.
        "lang": "id",        # minta deskripsi cuaca ("cerah berawan", dst)
                             # dalam Bahasa Indonesia langsung dari API-nya,
                             # jadi nggak perlu translate manual di kode kita.
    }

    response = requests.get(url, params=params)

    # Cek status_code: 200 artinya sukses. Kalau bukan 200 (misal 404 = kota
    # tidak ditemukan, 401 = API key salah), kita return pesan yang aman
    # dibaca LLM, bukan biarkan program crash gara-gara data yang diharapkan
    # ternyata tidak ada.
    if response.status_code != 200:
        return f"Data cuaca untuk {location} tidak tersedia (kemungkinan nama kota salah atau API key belum diisi)."

    data = response.json()

    # Struktur response OpenWeatherMap (format JSON dari dokumentasi resminya):
    # data["main"]["temp"] = suhu, data["weather"][0]["description"] = deskripsi,
    # data["main"]["humidity"] = persentase kelembapan
    suhu = data["main"]["temp"]
    deskripsi = data["weather"][0]["description"]
    kelembapan = data["main"]["humidity"]

    return (
        f"Cuaca di {location} saat ini {deskripsi}, suhu sekitar {suhu:.0f} "
        f"derajat Celsius, kelembapan {kelembapan} persen."
    )
