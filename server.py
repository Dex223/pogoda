import http.server
import socketserver
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

PORT = 8080


# === МОКОВЫЕ ДАННЫЕ (если API недоступен) ===
def get_mock_weather():
    now = datetime.now()
    hourly_times = []
    hourly_temps = []
    hourly_codes = []
    hourly_vis = []
    for i in range(24):
        t = now + timedelta(hours=i)
        hourly_times.append(t.strftime('%Y-%m-%dT%H:00'))
        hourly_temps.append(10 + i % 5)
        hourly_codes.append([0, 1, 2, 3, 61, 63][i % 6])
        hourly_vis.append(10000)

    daily_times = []
    daily_max = []
    daily_min = []
    daily_codes = []
    daily_precip = []
    daily_wind = []
    for i in range(7):
        d = now + timedelta(days=i)
        daily_times.append(d.strftime('%Y-%m-%d'))
        daily_max.append(15 + i % 4)
        daily_min.append(5 + i % 3)
        daily_codes.append([0, 1, 2, 3, 61, 63, 71][i % 7])
        daily_precip.append(i * 10)
        daily_wind.append(3 + i)

    return {
        'current': {
            'time': now.strftime('%Y-%m-%dT%H:00'),
            'temperature_2m': 12,
            'relative_humidity_2m': 68,
            'apparent_temperature': 10,
            'weather_code': 3,
            'wind_speed_10m': 4
        },
        'hourly': {
            'time': hourly_times,
            'temperature_2m': hourly_temps,
            'weather_code': hourly_codes,
            'visibility': hourly_vis
        },
        'daily': {
            'time': daily_times,
            'temperature_2m_max': daily_max,
            'temperature_2m_min': daily_min,
            'weather_code': daily_codes,
            'precipitation_probability_max': daily_precip,
            'wind_speed_10m_max': daily_wind
        }
    }


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API погоды
        if self.path.startswith('/api/weather'):
            print(f"[API] Запрос погоды: {self.path}")
            try:
                # Берём параметры из URL
                query = self.path.split('?', 1)[1] if '?' in self.path else ''
                params = urllib.parse.parse_qs(query)
                lat = params.get('latitude', ['59.93'])[0]
                lon = params.get('longitude', ['30.33'])[0]

                url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&hourly=temperature_2m,weather_code,visibility&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max&timezone=auto&forecast_days=7&wind_speed_unit=ms'

                print(f"[API] Обращаюсь к: {url}")
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                print(f"[API] Успех! Получено {len(data)} байт")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception as e:
                print(f"[API] Ошибка: {e}")
                print(f"[API] Отдаю моковые данные")
                mock = get_mock_weather()
                body = json.dumps(mock, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
                return

        # Поиск города
        elif self.path.startswith('/api/search'):
            print(f"[SEARCH] Запрос: {self.path}")
            try:
                query = self.path.split('?', 1)[1] if '?' in self.path else ''
                url = f'https://geocoding-api.open-meteo.com/v1/search?{query}'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                print(f"[SEARCH] Ошибка: {e}")
                # Моковые результаты поиска
                mock_results = {
                    'results': [
                        {'name': 'Санкт-Петербург', 'latitude': 59.93, 'longitude': 30.33, 'country': 'Россия',
                         'admin1': 'Санкт-Петербург'},
                        {'name': 'Москва', 'latitude': 55.75, 'longitude': 37.62, 'country': 'Россия',
                         'admin1': 'Москва'},
                        {'name': 'Казань', 'latitude': 55.79, 'longitude': 49.11, 'country': 'Россия',
                         'admin1': 'Татарстан'}
                    ]
                }
                body = json.dumps(mock_results, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(body)
            return

        # HTML файл
        super().do_GET()

    def log_message(self, format, *args):
        pass


print("=" * 50)
print("  ✅ Сервер погоды запущен!")
print(f"  🌐 Открой: http://localhost:{PORT}")
print("  ⚠️  Если API недоступен - будут демо-данные")
print("  🛑 Ctrl+C для остановки")
print("=" * 50)

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹ Остановлено")