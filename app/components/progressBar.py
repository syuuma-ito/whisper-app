import flet as ft


class ProgressBar(ft.Container):
    """プログレスバーを表示するコンポーネント

    Methods:
        update_value(value: float, label: str = ""): 進捗バーの値を更新
    """

    def __init__(self, value=0.0, label=""):
        super().__init__()
        self.expand = 1
        self.padding = 10

        self.progress_bar_element = ft.ProgressBar(value=value, expand=True)
        self.percent_text_element = ft.Text(
            f"{int(value * 100)}%", width=50, style=ft.TextThemeStyle.BODY_SMALL
        )
        self.label_text_element = ft.Text(label, style=ft.TextThemeStyle.BODY_SMALL)

        self.content = ft.Column(
            [
                ft.Row(
                    [
                        self.progress_bar_element,
                        self.percent_text_element,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                self.label_text_element,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def update_value(self, value: float, label: str = ""):
        """プログレスバーの値を更新する

        Args:
            value (float): 新しい進捗値（0.0から1.0の範囲）
        """
        if 0.0 <= value <= 1.0:
            self.progress_bar_element.value = value
            self.percent_text_element.value = f"{int(value * 100)}%"
            self.label_text_element.value = label
            self.update()
        else:
            raise ValueError("Value must be between 0.0 and 1.0")


if __name__ == "__main__":
    import time

    def main(page: ft.Page):
        progress_bar = ProgressBar(value=0, label="`処理中...`")
        page.add(progress_bar)

        while True:
            for i in range(1001):
                progress_bar.update_value(i / 1000, label=f"処理中... {i} / 1000")
                page.update()
                time.sleep(0.01)

    ft.app(target=main)
