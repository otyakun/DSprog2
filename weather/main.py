import flet as ft
import requests
from datetime import datetime, timedelta

# 定数定義
AREA_CODE_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"
WEATHER_ICON_URL = "https://www.jma.go.jp/bosai/forecast/img/"

# 関数定義
def get_area_list():

    #気象庁APIから地域リストを取得する
    try:
        response = requests.get(AREA_CODE_URL)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

def get_weather_forecast(area_code):
 
    #指定された地域コードの天気予報を取得する

    try:
        url = FORECAST_URL.format(area_code)
        response = requests.get(url)
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

def create_weather_card(date_str, weather_info):

    #天気予報カードを作成する

    weather = weather_info.get("weathers", ["-"])[0]
    weather_img_code = weather_info.get("weatherCodes", ["-"])[0]
    wind = weather_info.get("winds", ["-"])[0]
    temp_max = weather_info.get("temps", [[None, None]])[0][1]
    temp_min = weather_info.get("temps", [[None, None]])[0][0]

    weather_icon = ft.Image(
        src=f"{WEATHER_ICON_URL}/{weather_img_code}.png",
        width=50,
        height=50,
        fit=ft.ImageFit.CONTAIN
    ) if weather_img_code != "-" else ft.Text("No Icon")
    
    return ft.Card(
        elevation=5,
        content=ft.Container(
            padding=10,
            width=200,
            height=250,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Text(date_str, size=14),
                    weather_icon,
                    ft.Text(weather, size=16),
                    ft.Text(f"最高気温: {temp_max}℃" if temp_max else "最高気温: -", size=12),
                    ft.Text(f"最低気温: {temp_min}℃" if temp_min else "最低気温: -", size=12),
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
        weather_view.controls.clear() 

        if weather_data:
            forecasts = weather_data[0]["timeSeries"][0]["areas"][0] 
            # 今日から4日間の天気予報を取得
            for i in range(4):
                target_date = datetime.now() + timedelta(days=i)
                date_str = target_date.strftime("%Y-%m-%d")
                weather_view.controls.append(create_weather_card(date_str, forecasts))
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