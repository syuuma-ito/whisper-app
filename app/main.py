import queue
import threading
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import flet as ft
from components.filePicker import FilePicker
from components.logView import LogView
from components.progressBar import ProgressBar
from components.settings import Settings
from config.transcription_config import TranscriptionConfig
from flet import margin
from utils.torch import can_use_gpu
from whisper import transcription


class AppStatus(Enum):
    """アプリケーションのステータス"""

    WAITING = "待機中..."
    TRANSCRIBING = "文字起こし中..."
    COMPLETED = "完了"


class WhisperApp:
    """文字起こしアプリケーションのメインクラス"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.target_file: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.transcription_config = TranscriptionConfig.get_default_settings()
        self.current_status = AppStatus.WAITING

        # キューとスレッド管理
        self.message_queue = queue.Queue()
        self.transcription_thread: Optional[threading.Thread] = None
        self.queue_checker_thread: Optional[threading.Thread] = None
        self.should_stop_queue_checker = False
        self.should_stop_transcription = False
        self.is_transcribing = False

        self._setup_page()
        self._setup_components()
        self._setup_layout()
        self._setup_initial_logs()
        self._start_queue_checker()

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

        self.page.on_window_event = self._on_window_event

    def _setup_components(self) -> None:
        """コンポーネントの初期化と設定を行う"""
        self.log_view = LogView()
        self.progress_bar = ProgressBar(value=0.0)

        self.status_text = ft.Text(
            self.current_status.value,
            color=ft.Colors.GREY_600,
        )

        self.start_button = ft.FilledButton(
            "文字起こし開始",
            disabled=True,
            on_click=lambda _: self._run_transcription(),
        )

        self.stop_button = ft.FilledButton(
            "停止する",
            disabled=True,
            on_click=lambda _: self._stop_transcription(),
        )

        self._setup_file_pickers()

        self.transcription_settings_component = Settings(
            settings=self.transcription_config.to_dict(),
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
                                    [self.start_button, self.stop_button],
                                    spacing=10,
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
                        height=500,
                        expand=False,
                    ),
                    ft.Container(
                        content=self.progress_bar,
                        height=40,
                    ),
                    ft.Container(
                        content=self.status_text,
                        height=50,
                        margin=margin.only(left=10),
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

    def _start_queue_checker(self) -> None:
        """キューチェッカーを開始する"""
        self.should_stop_queue_checker = False
        self.queue_checker_thread = threading.Thread(
            target=self._queue_checker_worker, daemon=True
        )
        self.queue_checker_thread.start()

    def _queue_checker_worker(self) -> None:
        """キューからメッセージを取得してUIを更新する"""
        while not self.should_stop_queue_checker:
            try:
                message = self.message_queue.get(timeout=0.1)
                self._process_queue_message(message)
                self.message_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"キューチェッカーでエラーが発生しました: {e}")

    def _process_queue_message(self, message: Dict[str, Any]) -> None:
        """キューから受信したメッセージを処理する"""
        message_type = message.get("type")

        if message_type == "log":
            self.log_view.add_log(message["text"], message["level"])
        elif message_type == "progress":
            self.progress_bar.update_value(message["value"])
        elif message_type == "error":
            self.log_view.error(message["text"])
            self._update_status(AppStatus.WAITING)
        elif message_type == "status":
            status_name = message.get("status")
            if status_name:
                try:
                    status = AppStatus(status_name)
                    self._update_status(status)
                except ValueError:
                    print(f"不明なステータス: {status_name}")
        elif message_type == "transcription_started":
            self._update_status(AppStatus.TRANSCRIBING)
        elif message_type == "transcription_stopped":
            self._update_status(AppStatus.WAITING)
        elif message_type == "transcription_finished":
            self._update_status(AppStatus.COMPLETED)

        self.page.update()

    def _update_status(self, status: AppStatus) -> None:
        """アプリケーションのステータスを更新する"""
        self.current_status = status
        self.status_text.value = status.value

        color_map = {
            AppStatus.WAITING: ft.Colors.GREY_600,
            AppStatus.TRANSCRIBING: ft.Colors.BLUE_600,
            AppStatus.COMPLETED: ft.Colors.GREEN_600,
        }
        self.status_text.color = color_map.get(status, ft.Colors.GREY_600)

        self._update_button_states()

        self.page.update()

    def _update_button_states(self) -> None:
        """ステータスに基づいてボタンの状態を更新する"""
        if self.current_status == AppStatus.WAITING:
            self._update_start_button_state()
            self.stop_button.disabled = True
            self.stop_button.bgcolor = None
        elif self.current_status == AppStatus.TRANSCRIBING:
            self.start_button.disabled = True
            self.stop_button.disabled = False
            self.stop_button.bgcolor = ft.Colors.RED_300
        elif self.current_status == AppStatus.COMPLETED:
            self._update_start_button_state()
            self.stop_button.disabled = True
            self.stop_button.bgcolor = None

    def _on_window_event(self, e) -> None:
        """ウィンドウイベントのハンドラー"""
        if e.data == "close":
            self._cleanup()

    def _cleanup(self) -> None:
        """リソースのクリーンアップ"""
        if self.is_transcribing:
            self.should_stop_transcription = True

        self.should_stop_queue_checker = True

        if self.queue_checker_thread and self.queue_checker_thread.is_alive():
            self.queue_checker_thread.join(timeout=1.0)

        if self.transcription_thread and self.transcription_thread.is_alive():
            pass

    def _stop_transcription(self) -> None:
        """文字起こしを停止する"""
        self.should_stop_transcription = True
        self.log_view.add_log("文字起こしの停止を要求しました", "INFO")

    def _update_start_button_state(self, disabled: Optional[bool] = None) -> None:
        """スタートボタンの有効/無効状態を更新する"""
        if disabled is not None:
            self.start_button.disabled = disabled
        else:
            basic_conditions = bool(self.target_file and self.output_folder)

            language_valid = self.transcription_config.is_valid_language()

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

            # フォルダが選択されていない場合、ファイルのディレクトリを自動設定
            if not self.output_folder:
                file_directory = str(Path(file_path).parent)
                self.output_folder = file_directory
                self.output_folder_picker.set_selected_folder(file_directory)

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
        self.transcription_config = TranscriptionConfig.from_dict(settings)

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

        if self.transcription_thread and self.transcription_thread.is_alive():
            self.log_view.add_log("既に文字起こしが実行中です", "WARNING")
            return

        self.should_stop_transcription = False
        self.progress_bar.reset()

        self.transcription_thread = threading.Thread(
            target=lambda: transcription(
                self.transcription_config.to_dict(),
                target_file,
                output_folder,
                self.message_queue,
                lambda: self.should_stop_transcription,
            ),
            daemon=True,
        )
        self.transcription_thread.start()


def main(page: ft.Page):
    """アプリケーションのメイン関数"""
    app = WhisperApp(page)


if __name__ == "__main__":
    ft.app(main)
