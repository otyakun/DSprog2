import flet as ft
import requests
import datetime
import sqlite3

# データベースの初期化
def initialize_database():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    # 地域情報テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT UNIQUE,
            area_name TEXT
        )
    ''')
    # 天気予報情報テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT,
            date TEXT,
            weather TEXT,
            wind TEXT,
            max_temp TEXT,
            min_temp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# 地域リストの取得とデータベースへの格納
def get_area_list():
    AREA_CODE_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        response = requests.get(AREA_CODE_URL)
        response.raise_for_status()
        area_data = response.json()
        area_list = [{'area_code': code, 'area_name': info['name']}
                     for code, info in area_data.get('offices', {}).items()]
        return area_list
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return []

def store_area_list(area_list):
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT OR IGNORE INTO Areas (area_code, area_name)
        VALUES (:area_code, :area_name)
    ''', area_list)
    conn.commit()
    conn.close()

def get_areas_from_db():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('SELECT area_code, area_name FROM Areas')
    area_list = [{'area_code': row[0], 'area_name': row[1]} for row in cursor.fetchall()]
    conn.close()
    return area_list

# 天気予報の取得とデータベースへの格納
def get_weather_forecast(area_code):
    FORECAST_URL = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    try:
        response = requests.get(FORECAST_URL)
        response.raise_for_status()
        weather_data = response.json()

        if weather_data:
            weather_info = weather_data[0]["timeSeries"][0]["areas"][0]
            temp_info_section = next((ts for ts in weather_data[0]["timeSeries"] if 'temps' in ts["areas"][0]), None)

            if temp_info_section:
                temps = temp_info_section["areas"][0].get('temps', [])
                max_temp = temps[1] if len(temps) > 1 else "データ未取得"
                min_temp = temps[0] if len(temps) > 0 else "データ未取得"
            else:
                max_temp, min_temp = "データ未取得", "データ未取得"

            report_datetime = weather_data[0]["reportDatetime"]
            date = datetime.datetime.fromisoformat(report_datetime).strftime('%Y-%m-%d')

            forecast_data = {
                'area_code': area_code,
                'date': date,
                'weather': weather_info['weathers'][0],
                'wind': weather_info['winds'][0],
                'max_temp': max_temp,
                'min_temp': min_temp
            }
            return forecast_data
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

def store_forecast(forecast):
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Forecasts (area_code, date, weather, wind, max_temp, min_temp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (forecast['area_code'], forecast['date'], forecast['weather'],
          forecast['wind'], forecast['max_temp'], forecast['min_temp']))
    conn.commit()
    conn.close()

def get_forecast_from_db(area_code):
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, weather, wind, max_temp, min_temp
        FROM Forecasts
        WHERE area_code = ?
        ORDER BY id DESC LIMIT 1
    ''', (area_code,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'area_code': area_code,
            'date': row[0],
            'weather': row[1],
            'wind': row[2],
            'max_temp': row[3],
            'min_temp': row[4]
        }
    return None

def get_area_name(area_code):
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('SELECT area_name FROM Areas WHERE area_code = ?', (area_code,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ''

def weather_icon(weather):
    if "晴" in weather:
        return ft.icons.WB_SUNNY
    if "雨" in weather:
        return ft.icons.UMBRELLA
    if "曇" in weather:
        return ft.icons.WB_CLOUDY
    if "雪" in weather:
        return ft.icons.AC_UNIT
    # その他の天気にも対応するアイコンを追加できます
    return ft.icons.HELP_OUTLINE  # デフォルトのアイコン

def create_weather_card(forecast):
    return ft.Card(
        content=ft.Container(
            ft.Column([
                ft.Text(forecast['date'], size=18, weight=ft.FontWeight.BOLD),
                ft.Icon(weather_icon(forecast['weather']), size=48),
                ft.Text(forecast['weather'], size=14),
                ft.Row([
                    ft.Text(f"{forecast['min_temp']}°C", color=ft.Colors.BLUE, size=16),
                    ft.Text("/", size=16),
                    ft.Text(f"{forecast['max_temp']}°C", color=ft.Colors.RED, size=16)
                ])
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
        )
    )

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # データベースの初期化
    initialize_database()

    # 地域リストを取得してデータベースに格納
    area_list = get_area_list()
    if area_list:
        store_area_list(area_list)

    # データベースから地域リストを取得
    area_list = get_areas_from_db()
    if not area_list:
        page.add(ft.Text("地域情報が取得できませんでした。"))
        return

    # 地域一覧オプションを作成
    area_options = [
        ft.dropdown.Option(area["area_code"], area["area_name"])
        for area in area_list
    ]

    # 天気表示エリア
    weather_cards = ft.Column()

    # 天気情報を取得してUIに表示する関数
    def display_weather(area_code):
        forecast_list = []
        for _ in range(7):  # 1週間分のデータを取得
            forecast = get_forecast_from_db(area_code)
            if not forecast:
                forecast = get_weather_forecast(area_code)
                if forecast:
                    store_forecast(forecast)
            if forecast:
                forecast_list.append(forecast)

        weather_cards.controls.clear()
        for forecast in forecast_list:
            weather_cards.controls.append(create_weather_card(forecast))
        page.update()

    # 地域が変更されたときのイベントハンドラ
    def on_area_change(e):
        display_weather(e.control.value)

    # ドロップダウンリスト
    area_dropdown = ft.Dropdown(
        options=area_options,
        label="地域を選択",
        on_change=on_area_change
    )

    # ページにコンポーネントを追加
    page.add(area_dropdown, weather_cards)

# アプリケーションの実行
if __name__ == "__main__":
    ft.app(target=main)