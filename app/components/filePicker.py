import flet as ft


ALLOWED_EXTENSIONS = [
    "mp3",
    "wav",
    "m4a",
    # "mp4",
    # "mov",
]


class FilePicker(ft.Container):
    def __init__(
        self,
        is_folder: bool = False,
        directory: str = "",
        on_result=None,
    ):
        super().__init__()
        self.padding = 10

        self.is_folder = is_folder
        self.directory = directory
        self.on_result = on_result

        self.selected_file = None
        self.selected_folder = None

        self.file_picker_element = ft.FilePicker(
            on_result=self._on_file_picker_result,
        )

        self.label_text_element = ft.Text(
            "選択されていません",
            theme_style=ft.TextThemeStyle.BODY_SMALL,
        )

        self.content = ft.Column(
            [
                ft.OutlinedButton(
                    "フォルダを選択" if is_folder else "ファイルを選択",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=self._on_click,
                ),
                self.label_text_element,
            ],
        )

    def _on_file_picker_result(self, e: ft.FilePickerResultEvent):
        """ファイル選択結果のハンドラー"""
        if self.on_result:
            self.on_result(e)
        else:
            if e.files:
                self.selected_file = e.files[0].path
                self.label_text_element.value = (
                    f"選択されたファイル: {self.selected_file}"
                )
                self.update()
            elif e.path:
                self.selected_folder = e.path
                self.label_text_element.value = (
                    f"選択されたフォルダ: {self.selected_folder}"
                )
                self.update()

    def _on_click(self, e: ft.ControlEvent):
        """ファイル選択ダイアログを開く"""
        if self.is_folder:
            self.file_picker_element.get_directory_path(
                dialog_title="フォルダを選択",
            )
        else:
            self.file_picker_element.pick_files(
                allowed_extensions=ALLOWED_EXTENSIONS,
                dialog_title="ファイルを選択",
            )

    def get_file_picker_overlay(self):
        return self.file_picker_element


if __name__ == "__main__":

    def main(page: ft.Page):
        file_picker = FilePicker(is_folder=False, directory="")
        page.add(file_picker)
        page.overlay.append(file_picker.get_file_picker_overlay())
        page.update()

    ft.app(target=main)
