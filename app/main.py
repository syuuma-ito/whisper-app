import flet as ft
from pathlib import Path

from components.logView import LogView
from components.progressBar import ProgressBar
from components.filePicker import FilePicker
from components.settings import Settings
from utils.torch import can_use_gpu
from whisper import transcription


def main(page: ft.Page):
    #  アプリケーションの初期設定
    page.title = "文字起こしアプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {
        "ZenMaruGothic": "./assets/fonts/ZenMaruGothic-Regular.ttf",
    }
    page.theme = ft.Theme(font_family="ZenMaruGothic")

    #  文字起こしの設定
    transcription_settings = {
        "model": "medium",
        "compute_type": "int8",
        "device": "CPU",
    }
    target_file = None
    output_folder = None

    #  コンポーネントの初期化
    log_view = LogView()
    progress_bar = ProgressBar(value=0.0, label="")

    def disabled_start_button(state: bool):
        """スタートボタンの状態を変更する"""
        nonlocal start_button
        start_button.disabled = state

        page.update()

    start_button = ft.FilledButton(
        "文字起こし開始",
        disabled=True,
        on_click=lambda _: run_transcription(),
    )

    def on_file_selected(file_path):
        nonlocal target_file, output_folder, start_button
        target_file = file_path
        log_view.add_log(f"選択されたファイル: {file_path}", "DEBUG")

        if output_folder and target_file:
            disabled_start_button(False)

    target_file_picker = FilePicker(
        is_folder=False,
        directory="",
        on_change=on_file_selected,
    )
    page.overlay.append(target_file_picker.get_file_picker_overlay())

    def on_folder_selected(folder_path):
        nonlocal target_file, output_folder, start_button
        output_folder = folder_path
        log_view.add_log(f"出力フォルダ: {folder_path}", "DEBUG")

        if target_file and output_folder:
            disabled_start_button(False)

    output_folder_picker = FilePicker(
        is_folder=True,
        directory="",
        on_change=on_folder_selected,
    )
    page.overlay.append(output_folder_picker.get_file_picker_overlay())

    # 文字起こしの設定
    def on_settings_change(settings):
        nonlocal transcription_settings
        transcription_settings = settings
        log_view.add_log(f"設定が変更されました: {settings}", "DEBUG")

    transcription_settings_component = Settings(
        settings=transcription_settings,
        on_change=on_settings_change,
    )

    def run_transcription():
        nonlocal target_file, output_folder, transcription_settings, log_view, progress_bar, disabled_start_button

        page.run_thread(
            lambda: transcription(
                transcription_settings,
                target_file,
                output_folder,
                log_view,
                progress_bar,
                disabled_start_button,
            )
        )

    #
    #
    #  ページのレイアウト設定
    #
    #
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
                            ft.Text(
                                "1.ファイルを選択",
                                theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                            ),
                            target_file_picker,
                            ft.Text(
                                "2.設定",
                                theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                            ),
                            transcription_settings_component,
                            ft.Text(
                                "3.出力フォルダを選択",
                                theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                            ),
                            output_folder_picker,
                            ft.Text(
                                "4.文字起こし開始",
                                theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                start_button,
                                            ]
                                        ),
                                    ]
                                ),
                                margin=10,
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

    if can_use_gpu():
        log_view.add_log("GPUが使用可能です", "INFO")
    else:
        log_view.add_log("GPUは使用できません", "WARNING")
        log_view.add_log("CPUでは処理が遅くなる可能性があります", "WARNING")


if __name__ == "__main__":
    ft.app(main)
