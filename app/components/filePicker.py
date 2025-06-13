import flet as ft


ALLOWED_EXTENSIONS = [
    "mp3",
    "wav",
    "m4a",
    #
    # TODO: 動画ファイルも対応するように
    # "mp4",
    # "mov",
]


class FilePicker(ft.Container):
    def __init__(
        self,
        is_folder: bool = False,
        directory: str = "",
        on_change=None,
    ):
        super().__init__()
        self.padding = 10

        self.is_folder = is_folder
        self.directory = directory
        self._on_change = on_change

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
        if e.files:
            self.selected_file = e.files[0].path
            self.label_text_element.value = f"選択されたファイル: {self.selected_file}"
            self.selected_folder = None

            if self._on_change:
                self._on_change(self.selected_file)
        elif e.path:
            self.selected_folder = e.path
            self.label_text_element.value = (
                f"選択されたフォルダ: {self.selected_folder}"
            )
            self.selected_file = None

            if self._on_change:
                self._on_change(self.selected_folder)

        self.update()

    def _on_click(self, e: ft.ControlEvent):
        """ファイル選択ダイアログを開く"""
        if self.is_folder:
            self.file_picker_element.get_directory_path(
                dialog_title="フォルダを選択",
            )

            # TODO: ファイルピッカーを開くときのデフォルトのディレクトリを設定する
        else:
            self.file_picker_element.pick_files(
                allowed_extensions=ALLOWED_EXTENSIONS,
                dialog_title="ファイルを選択",
            )

    def get_selected_file(self):
        return self.selected_file

    def get_selected_folder(self):
        return self.selected_folder

    def get_selected_item(self):
        return self.selected_file if not self.is_folder else self.selected_folder

    def get_file_picker_overlay(self):
        return self.file_picker_element

    def set_selected_file(self, file_path: str):
        """選択されたファイルを設定する"""
        self.selected_file = file_path
        self.label_text_element.value = f"選択されたファイル: {file_path}"
        if self._on_change:
            self._on_change(file_path)
        self.update()

    def set_selected_folder(self, folder_path: str):
        """選択されたフォルダを設定する"""
        self.selected_folder = folder_path
        self.label_text_element.value = f"選択されたフォルダ: {folder_path}"
        if self._on_change:
            self._on_change(folder_path)
        self.update()


if __name__ == "__main__":

    def on_file_selected(file_path):
        print(f"Selected file: {file_path}")

    def main(page: ft.Page):
        file_picker = FilePicker(
            is_folder=False, directory="", on_change=on_file_selected
        )
        page.add(file_picker)
        page.overlay.append(file_picker.get_file_picker_overlay())
        page.update()

    ft.app(target=main)
