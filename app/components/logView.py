from datetime import datetime

import flet as ft

import logging
from rich.logging import RichHandler

log = logging.getLogger("app_logger")
log.setLevel(logging.DEBUG)

if not log.hasHandlers():
    rich_handler = RichHandler(rich_tracebacks=True)
    rich_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    rich_handler.setFormatter(formatter)
    log.addHandler(rich_handler)


color_map = {
    "INFO": ft.Colors.BLUE_600,
    "WARNING": ft.Colors.AMBER_600,
    "ERROR": ft.Colors.RED_600,
    "DEBUG": ft.Colors.GREY_600,
}


class LogView(ft.ListView):
    """アプリケーションのログを表示するコンポーネント

    Methods:
        add_log(message: str, level: str = "DEBUG"): ログメッセージを追加
        clear_logs(): ログをクリア
    """

    def __init__(self):
        super().__init__()
        self.expand = 1
        self.spacing = 5
        self.auto_scroll = True
        self.height = 300

    def add_log(self, message: str, level: str = "DEBUG"):
        """ログメッセージを追加するメソッド
        Args:
            message (str): ログメッセージ
            level (str): ログレベル（"DEBUG", "INFO", "WARNING", "ERROR"）
        """
        color = color_map.get(level, ft.Colors.GREY_600)

        log_line = ft.Row(
            [
                ft.Text(f"[{level}]", color=color, width=80),
                ft.Text(message, color=color, expand=1),
                ft.Text(
                    datetime.now().strftime("%H:%M:%S"),
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.END,
                    width=80,
                ),
            ]
        )

        self.controls.append(log_line)
        self.update()

        if level == "ERROR":
            log.error(message)
        elif level == "WARNING":
            log.warning(message)
        elif level == "INFO":
            log.info(message)
        else:
            log.debug(message)

    def clear_logs(self):
        """ログをクリアするメソッド"""
        self.controls.clear()
        self.update()


if __name__ == "__main__":
    import time

    def main(page: ft.Page):
        log_view = LogView()
        page.add(log_view)

        # Example usage
        log_view.add_log("アプリケーションが起動しました", "INFO")
        log_view.add_log("デバッグ情報", "DEBUG")
        log_view.add_log("警告メッセージ", "WARNING")
        log_view.add_log("エラーメッセージ", "ERROR")

        for i in range(10):
            log_view.add_log(f"ログメッセージ {i + 1}", "INFO")
            time.sleep(0.5)

    ft.app(main)
