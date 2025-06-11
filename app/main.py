from datetime import datetime
from pathlib import Path
import time
import flet as ft

from components.logView import LogView
from components.progressBar import ProgressBar

BASE_DIR = Path(__file__).resolve().parent.parent


def main(page: ft.Page):
    page.title = "文字起こしアプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {
        "ZenMaruGothic": "./assets/fonts/ZenMaruGothic-Regular.ttf",
    }
    page.theme = ft.Theme(font_family="ZenMaruGothic")

    log_view = LogView()
    progress_bar = ProgressBar(value=0.0, label="処理中...")

    page.add(
        ft.Column(
            [
                ft.Text(
                    "文字起こしアプリ",
                    theme_style=ft.TextThemeStyle.HEADLINE_LARGE,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "[ 設定 ]",
                                theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                            ),
                        ]
                    ),
                    margin=10,
                    padding=10,
                    border=ft.border.all(1, ft.Colors.BLACK38),
                    border_radius=10,
                    expand=1,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "[ ログ ]",
                                theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                            ),
                            log_view,
                            progress_bar,
                        ]
                    ),
                    margin=10,
                    padding=10,
                    border=ft.border.all(1, ft.Colors.BLACK38),
                    border_radius=10,
                    expand=1,
                ),
            ]
        ),
    )
    log_view.add_log("アプリケーションが起動しました", "INFO")
    log_view.add_log("デバッグ情報", "DEBUG")
    log_view.add_log("警告メッセージ", "WARNING")
    log_view.add_log("エラーメッセージ", "ERROR")

    for i in range(100):
        log_view.add_log(f"ログメッセージ {i + 1}", "DEBUG")
        progress_bar.update_value(i / 100, label=f"処理中... {i + 1} / 100")
        time.sleep(0.2)


if __name__ == "__main__":
    ft.app(main)
