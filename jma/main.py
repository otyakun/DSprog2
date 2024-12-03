import flet as ft
import requests
from datetime import datetime, timedelta

# 気象庁のAPIのエンドポイント
AREA_CODE_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

# 天気アイコンのURL
WEATHER_ICON_URL = "https://www.jma.go.jp/bosai/forecast/img/"

# 地域リストの取得
def get_area_list():
    try:
        response = requests.get(AREA_CODE_URL)
        response.raise_for_status()  # ステータスコードが200でない場合は例外を発生させる
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

# 天気予報の取得
def get_weather_forecast(area_code):
    try:
        url = FORECAST_URL.format(area_code)
        response = requests.get(url)
        response.raise_for_status()  # ステータスコードが200でない場合は例外を発生させる
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

# 天気予報カードの作成
def create_weather_card(date_str, weather_info):
    weather = weather_info.get("weathers", ["-"])[0]
    weather_img = weather_info.get("weatherCodes", ["-"])[0]
    temp_max = weather_info.get("temps", [["-", "-"]])[0][1]
    temp_min = weather_info.get("temps", [["-", "-"]])[0][0]

    if weather_img != "-":
        weather_icon = ft.Image(
            src=f"{WEATHER_ICON_URL}/{weather_img}.png",
            width=50,
            height=50,
            fit=ft.ImageFit.CONTAIN
        )
    else:
        weather_icon = ft.Text("No Icon")

    return ft.Card(
        elevation=5,
        content=ft.Container(
            padding=10,
            width=150,
            height=200,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Text(date_str, size=14),
                    weather_icon,
                    ft.Text(weather, size=16),
                    ft.Text(f"最高気温: {temp_max}℃", size=12),
                    ft.Text(f"最低気温: {temp_min}℃", size=12),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
    )

# Fletアプリケーションの定義
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.vertical_alignment = "start"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.bgcolor = ft.colors.BLUE_GREY_50
    
    # 地域リスト取得
    area_list = get_area_list()
    if not area_list:
        print("地域リストの取得に失敗しました。")
        return
    
    # 地域一覧オプションを作成
    area_options = [
        ft.dropdown.Option(text=info["name"], key=code)
        for code, info in area_list.get("offices", {}).items()
    ]
    
    # ドロップダウンリスト
    area_dropdown = ft.Dropdown(
        options=area_options, 
        label="地域を選択", 
        width=300
    )

    # 天気表示エリア
    weather_view = ft.Row(wrap=True, spacing=10)

    # ドロップダウンリストのイベントハンドラ
    def on_area_change(e):
        area_code = area_dropdown.value
        weather_data = get_weather_forecast(area_code)
        weather_view.controls.clear() # 以前の天気情報をクリア

        if weather_data:
            # 今日から4日間の天気予報を取得
            for i in range(4):
                target_date = datetime.now() + timedelta(days=i)
                date_str = target_date.strftime("%Y-%m-%d")
                weather_view.controls.append(create_weather_card(date_str, weather_data[0]["timeSeries"][0]["areas"][0]))
        else:
            weather_view.controls.append(ft.Text("天気情報が取得できませんでした。"))
        page.update()

    area_dropdown.on_change = on_area_change

    # ページにコンポーネントを追加
    page.add(
        ft.Column([
            area_dropdown,
            weather_view
        ])
    )

# アプリケーションの実行
ft.app(target=main)