"""
tools/ — Package berisi semua "tool" (fungsi) yang bisa dipanggil LLM lewat
function calling: cek cuaca (weather_tool.py), kontrol musik (music_tool.py),
dan skema yang mendaftarkan semuanya ke LLM (schema.py).

File __init__.py ini sengaja dikosongkan isinya — keberadaannya aja yang
penting, supaya Python mengenali folder tools/ sebagai package yang bisa
di-import (contoh: `from tools.weather_tool import get_weather`).
"""
