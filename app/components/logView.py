import logging
from datetime import datetime

import flet as ft
from rich.logging import RichHandler

LOG_LEVELS = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "WARNING",
    "ERROR": "ERROR",
}

COLOR_MAP = {
    LOG_LEVELS["INFO"]: ft.Colors.BLUE_600,
    LOG_LEVELS["WARNING"]: ft.Colors.AMBER_600,
    LOG_LEVELS["ERROR"]: ft.Colors.RED_600,
    LOG_LEVELS["DEBUG"]: ft.Colors.GREY_600,
}

log = logging.getLogger("app_logger")
log.setLevel(logging.DEBUG)

if not log.hasHandlers():
    rich_handler = RichHandler(rich_tracebacks=True)
    rich_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    rich_handler.setFormatter(formatter)
    log.addHandler(rich_handler)


class LogView(ft.ListView):
    """アプリケーションのログを表示するコンポーネント

    Methods:
        add_log(message: str, level: str = "DEBUG"): ログメッセージを追加
        clear_logs(): ログをクリア
        info(message: str): INFOレベルのログを追加
        warning(message: str): WARNINGレベルのログを追加
        error(message: str): ERRORレベルのログを追加
        debug(message: str): DEBUGレベルのログを追加
    """

    def __init__(self, max_logs: int = 1000):
        super().__init__()
        self.expand = False  # 親コンテナの高さに合わせる
        self.spacing = 5
        self.auto_scroll = True
        self.max_logs = max_logs

    def _normalize_log_level(self, level: str) -> str:
        """ログレベルを正規化する"""
        normalized_level = level.upper()
        if normalized_level not in LOG_LEVELS:
            normalized_level = LOG_LEVELS["DEBUG"]
        return normalized_level

    def _get_log_color(self, level: str) -> ft.Colors:
        """ログレベルに対応する色を取得する"""
        normalized_level = self._normalize_log_level(level)
        return COLOR_MAP.get(normalized_level, ft.Colors.GREY_600)

    def _create_log_line(self, message: str, level: str) -> ft.Row:
        """ログ行を作成する"""
        normalized_level = self._normalize_log_level(level)
        color = self._get_log_color(level)
        timestamp = datetime.now().strftime("%H:%M:%S")

        return ft.Row(
            [
                ft.Text(f"[{normalized_level}]", color=color, width=80),
                ft.Text(message, color=color, expand=1),
                ft.Text(
                    timestamp,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.END,
                    width=80,
                ),
            ]
        )

    def _trim_logs_if_needed(self) -> None:
        """ログ数が上限を超えた場合に古いログを削除する"""
        if len(self.controls) > self.max_logs:
            remove_count = len(self.controls) // 5
            self.controls = self.controls[remove_count:]

    def add_log(self, message: str, level: str = LOG_LEVELS["DEBUG"]) -> None:
        """ログメッセージを追加する

        Args:
            message (str): ログメッセージ
            level (str): ログレベル（"DEBUG", "INFO", "WARNING", "ERROR"）
        """
        try:
            if not message:
                return

            log_line = self._create_log_line(message, level)
            self.controls.append(log_line)

            self._trim_logs_if_needed()

            self.update()

            normalized_level = self._normalize_log_level(level)
            if normalized_level == LOG_LEVELS["ERROR"]:
                log.error(message)
            elif normalized_level == LOG_LEVELS["WARNING"]:
                log.warning(message)
            elif normalized_level == LOG_LEVELS["INFO"]:
                log.info(message)
            else:
                log.debug(message)

        except Exception as e:
            print(f"ログ出力エラー: {e}")

    def clear_logs(self) -> None:
        """ログをクリアする"""
        try:
            self.controls.clear()
            self.update()
        except Exception as e:
            print(f"ログクリアエラー: {e}")

    def info(self, message: str) -> None:
        """INFOレベルのログを追加する"""
        self.add_log(message, LOG_LEVELS["INFO"])

    def warning(self, message: str) -> None:
        """WARNINGレベルのログを追加する"""
        self.add_log(message, LOG_LEVELS["WARNING"])

    def error(self, message: str) -> None:
        """ERRORレベルのログを追加する"""
        self.add_log(message, LOG_LEVELS["ERROR"])

    def debug(self, message: str) -> None:
        """DEBUGレベルのログを追加する"""
        self.add_log(message, LOG_LEVELS["DEBUG"])


if __name__ == "__main__":
    import time

    def main(page: ft.Page):
        page.title = "LogView Component Test"

        log_view = LogView()
        page.add(log_view)

        log_view.add_log("アプリケーションが起動しました", "INFO")
        log_view.add_log("デバッグ情報", "DEBUG")
        log_view.add_log("警告メッセージ", "WARNING")
        log_view.add_log("エラーメッセージ", "ERROR")

        for i in range(10):
            log_view.add_log(f"ログメッセージ {i + 1}", "INFO")
            time.sleep(0.5)

    ft.app(main)
