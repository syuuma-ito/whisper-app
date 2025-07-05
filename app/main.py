from pathlib import Path
from typing import Any, Dict, Optional

import flet as ft
from components.filePicker import FilePicker
from components.logView import LogView
from components.progressBar import ProgressBar
from components.settings import Settings
from utils.torch import can_use_gpu
from whisper import transcription


class WhisperApp:
    """文字起こしアプリケーションのメインクラス"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.target_file: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.transcription_settings = self._get_default_settings()

        self._setup_page()
        self._setup_components()
        self._setup_layout()
        self._setup_initial_logs()

    def _setup_page(self) -> None:
        """ページの初期設定を行う"""
        self.page.title = "文字起こしアプリ"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.fonts = {
            "ZenMaruGothic": "./app/assets/fonts/ZenMaruGothic-Regular.ttf",
        }
        self.page.theme = ft.Theme(font_family="ZenMaruGothic")

        self.page.window.height = 800
        self.page.window.width = 1200

    def _get_default_settings(self) -> Dict[str, Any]:
        """デフォルトの文字起こし設定を取得する"""
        return {
            "model": "large-v3-turbo",
            "compute_type": "float16" if can_use_gpu() else "float32",
            "device": "GPU" if can_use_gpu() else "CPU",
            "language": "auto",
        }

    def _setup_components(self) -> None:
        """コンポーネントの初期化と設定を行う"""
        self.log_view = LogView()
        self.progress_bar = ProgressBar(value=0.0, label="")

        self.start_button = ft.FilledButton(
            "文字起こし開始",
            disabled=True,
            on_click=lambda _: self._run_transcription(),
        )

        self._setup_file_pickers()

        self.transcription_settings_component = Settings(
            settings=self.transcription_settings,
            on_change=self._on_settings_change,
        )

    def _setup_file_pickers(self) -> None:
        """ファイル選択コンポーネントを設定する"""
        self.target_file_picker = FilePicker(
            is_folder=False,
            directory="",
            on_change=self._on_file_selected,
        )
        self.page.overlay.append(self.target_file_picker.get_file_picker_overlay())

        self.output_folder_picker = FilePicker(
            is_folder=True,
            directory="",
            on_change=self._on_folder_selected,
        )
        self.page.overlay.append(self.output_folder_picker.get_file_picker_overlay())

    def _setup_layout(self) -> None:
        """ページのレイアウトを設定する"""
        self.page.add(
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
                    self._create_settings_panel(),
                    self._create_log_panel(),
                ]
            ),
        )

    def _create_settings_panel(self) -> ft.Container:
        """設定パネルを作成する"""
        return ft.Container(
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
                    self.target_file_picker,
                    ft.Text(
                        "2.設定",
                        theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                    ),
                    self.transcription_settings_component,
                    ft.Text(
                        "3.出力フォルダを選択",
                        theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                    ),
                    self.output_folder_picker,
                    ft.Text(
                        "4.文字起こし開始",
                        theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [self.start_button],
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
            height=650,
        )

    def _create_log_panel(self) -> ft.Container:
        """ログパネルを作成する"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            "[ ログ ]",
                            theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                        ),
                        height=60,
                    ),
                    ft.Container(
                        content=self.log_view,
                        height=510,
                        expand=False,
                    ),
                    ft.Container(
                        content=self.progress_bar,
                        height=80,
                    ),
                ],
                spacing=0,
            ),
            margin=10,
            padding=10,
            border=ft.border.all(1, ft.Colors.BLACK38),
            border_radius=10,
            expand=1,
            height=650,
        )

    def _setup_initial_logs(self) -> None:
        """初期ログを設定する"""
        self.log_view.add_log("アプリケーションが起動しました", "INFO")

        if can_use_gpu():
            self.log_view.add_log("GPUが使用可能です", "INFO")
        else:
            self.log_view.add_log("GPUは使用できません", "WARNING")
            self.log_view.add_log("CPUでは処理が遅くなる可能性があります", "WARNING")

    def _update_start_button_state(self, disabled: Optional[bool] = None) -> None:
        """スタートボタンの有効/無効状態を更新する"""
        if disabled is not None:
            self.start_button.disabled = disabled
        else:
            basic_conditions = bool(self.target_file and self.output_folder)

            language_valid = True
            if "language" in self.transcription_settings:
                language = self.transcription_settings["language"]
                if language == "":
                    language_valid = False

            is_enabled = basic_conditions and language_valid
            self.start_button.disabled = not is_enabled
        self.page.update()

    def _disabled_start_button(self, disabled: bool) -> None:
        """スタートボタンの有効/無効状態を設定する（コールバック用）"""
        self._update_start_button_state(disabled)

    def _on_file_selected(self, file_path: str) -> None:
        """ファイル選択時のハンドラー"""
        try:
            if not Path(file_path).exists():
                self.log_view.error(f"ファイルが見つかりません: {file_path}")
                return

            self.target_file = file_path
            self.log_view.add_log(f"選択されたファイル: {file_path}", "DEBUG")
            self._update_start_button_state()

        except Exception as e:
            self.log_view.error(f"ファイル選択中にエラーが発生しました: {e}")

    def _on_folder_selected(self, folder_path: str) -> None:
        """フォルダ選択時のハンドラー"""
        try:
            if not Path(folder_path).exists():
                self.log_view.error(f"フォルダが見つかりません: {folder_path}")
                return

            self.output_folder = folder_path
            self.log_view.add_log(f"出力フォルダ: {folder_path}", "DEBUG")
            self._update_start_button_state()

        except Exception as e:
            self.log_view.error(f"フォルダ選択中にエラーが発生しました: {e}")

    def _on_settings_change(self, settings: Dict[str, Any]) -> None:
        """設定変更時のハンドラー"""
        self.transcription_settings = settings
        self.log_view.add_log(f"設定が変更されました: {settings}", "DEBUG")
        self._update_start_button_state()

    def _run_transcription(self) -> None:
        """文字起こしを実行する"""
        if not self.target_file or not self.output_folder:
            self.log_view.error("ファイルとフォルダが選択されていません")
            return

        target_file = self.target_file
        output_folder = self.output_folder

        if not isinstance(target_file, str) or not isinstance(output_folder, str):
            self.log_view.error("ファイルまたはフォルダのパスが無効です")
            return

        self.page.run_thread(
            lambda: transcription(
                self.transcription_settings,
                target_file,
                output_folder,
                self.log_view,
                self.progress_bar,
                self._update_start_button_state,
            )
        )


def main(page: ft.Page):
    """アプリケーションのメイン関数"""
    app = WhisperApp(page)


if __name__ == "__main__":
    ft.app(main)
