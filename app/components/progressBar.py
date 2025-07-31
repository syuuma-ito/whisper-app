from typing import Optional

import flet as ft


class ProgressBar(ft.Container):
    """プログレスバーを表示するコンポーネント

    Methods:
        update_value(value: float, label: str = ""): 進捗バーの値を更新
        reset(): プログレスバーをリセット
        set_indeterminate(): 不定プログレスバーに設定
    """

    def __init__(self, value: float = 0.0, height: Optional[int] = None):
        super().__init__()
        self.expand = False  # 親コンテナの高さに合わせる
        self.padding = 10

        self._validate_value(value)

        self._setup_ui_components(value)
        self._setup_layout()

        if height:
            self.height = height

    def _validate_value(self, value: float) -> None:
        """進捗値を検証する"""
        if value < 0.0 or value > 1.0:
            raise ValueError("Value must be between 0.0 and 1.0")

    def _setup_ui_components(self, value: float) -> None:
        """UIコンポーネントを初期化する"""
        self.progress_bar_element = ft.ProgressBar(
            value=value,
            expand=True,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.GREY_300,
        )

        self.percent_text_element = ft.Text(
            f"{int(value * 100)}%",
            width=50,
            style=ft.TextThemeStyle.BODY_SMALL,
            text_align=ft.TextAlign.CENTER,
        )

    def _setup_layout(self) -> None:
        """レイアウトを設定する"""
        self.content = ft.Row(
            [
                self.progress_bar_element,
                self.percent_text_element,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def update_value(self, value: float) -> None:
        """プログレスバーの値を更新する

        Args:
            value (float): 新しい進捗値（0.0から1.0の範囲）
        """
        try:
            self._validate_value(value)

            self.progress_bar_element.value = value
            self.percent_text_element.value = f"{int(value * 100)}%"

            self.update()

        except ValueError as e:
            print(f"プログレスバー更新エラー: {e}")
        except Exception as e:
            print(f"予期しないエラー: {e}")

    def reset(self) -> None:
        """プログレスバーをリセットする"""
        try:
            self.update_value(0.0)
        except Exception as e:
            print(f"プログレスバーリセットエラー: {e}")

    def set_indeterminate(self) -> None:
        """不定プログレスバーに設定する"""
        try:
            self.progress_bar_element.value = None  # 不定プログレスバー
            self.percent_text_element.value = ""
            self.update()
        except Exception as e:
            print(f"不定プログレスバー設定エラー: {e}")

    def set_determinate(self, value: float = 0.0) -> None:
        """確定プログレスバーに設定する"""
        try:
            self.update_value(value)
        except Exception as e:
            print(f"確定プログレスバー設定エラー: {e}")

    def get_value(self) -> float:
        """現在の進捗値を取得する"""
        return self.progress_bar_element.value or 0.0

    def set_color(self, color: ft.Colors) -> None:
        """プログレスバーの色を設定する"""
        try:
            self.progress_bar_element.color = color
            self.update()
        except Exception as e:
            print(f"色設定エラー: {e}")


if __name__ == "__main__":
    import time

    def main(page: ft.Page):
        page.title = "ProgressBar Component Test"

        progress_bar = ProgressBar(value=0)
        page.add(progress_bar)

        for i in range(101):
            progress_bar.update_value(i / 100)
            page.update()
            time.sleep(0.05)

    ft.app(target=main)
