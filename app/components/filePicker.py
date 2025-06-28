from pathlib import Path
from typing import Callable, List, Optional, Set

import flet as ft

SUPPORTED_AUDIO_EXTENSIONS: Set[str] = {
    "mp3",
    "wav",
    "m4a",
    "flac",
    "aac",
    "ogg",
    "wma",
}

SUPPORTED_VIDEO_EXTENSIONS: Set[str] = {
    "mp4",
    "mov",
    "avi",
    "mkv",
    "wmv",
    "flv",
    "webm",
}

ALLOWED_EXTENSIONS: List[str] = list(
    SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS
)


class FilePickerError(Exception):
    """ファイル選択処理中のエラーを表す例外クラス"""

    pass


class FilePicker(ft.Container):
    """ファイルまたはフォルダを選択するコンポーネント"""

    def __init__(
        self,
        is_folder: bool = False,
        directory: str = "",
        on_change: Optional[Callable[[str], None]] = None,
        allowed_extensions: Optional[List[str]] = None,
    ):
        super().__init__()
        self.padding = 10

        self.is_folder = is_folder
        self.directory = directory
        self._on_change = on_change
        self.allowed_extensions = allowed_extensions or ALLOWED_EXTENSIONS

        self.selected_file: Optional[str] = None
        self.selected_folder: Optional[str] = None

        self._setup_ui_components()
        self._setup_file_picker()

    def _setup_ui_components(self) -> None:
        """UIコンポーネントを初期化する"""
        self.file_picker_element = ft.FilePicker(
            on_result=self._on_file_picker_result,
        )

        self.label_text_element = ft.Text(
            "選択されていません",
            theme_style=ft.TextThemeStyle.BODY_SMALL,
            color=ft.Colors.GREY_600,
        )

        self.content = ft.Column(
            [
                ft.OutlinedButton(
                    "フォルダを選択" if self.is_folder else "ファイルを選択",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=self._on_click,
                ),
                self.label_text_element,
            ],
            spacing=5,
        )

    def _setup_file_picker(self) -> None:
        """ファイルピッカーの設定を行う"""
        pass

    def _validate_file_extension(self, file_path: str) -> bool:
        """ファイル拡張子を検証する"""
        if self.is_folder:
            return True

        file_extension = Path(file_path).suffix.lower().lstrip(".")
        return file_extension in self.allowed_extensions

    def _on_file_picker_result(self, e: ft.FilePickerResultEvent) -> None:
        """ファイル選択結果のハンドラー"""
        if e.files:
            selected_path = e.files[0].path

            if not self._validate_file_extension(selected_path):
                self.label_text_element.value = f"エラー: サポートされていないファイル形式です: {Path(selected_path).suffix}"
                self.label_text_element.color = ft.Colors.RED_600
                self.update()
                return

            self.selected_file = selected_path
            self.selected_folder = None
            self.label_text_element.value = (
                f"選択されたファイル: {Path(selected_path).name}"
            )

            if self._on_change:
                self._on_change(selected_path)

        elif e.path:
            selected_path = e.path

            if not Path(selected_path).is_dir():
                self.label_text_element.value = (
                    f"エラー: 選択されたパスはフォルダではありません: {selected_path}"
                )
                self.label_text_element.color = ft.Colors.RED_600
                self.update()
                return

            self.selected_folder = selected_path
            self.selected_file = None
            self.label_text_element.value = (
                f"選択されたフォルダ: {Path(selected_path).name}"
            )

            if self._on_change:
                self._on_change(selected_path)

        self.update()

    def _on_click(self, e: ft.ControlEvent) -> None:
        """ファイル選択ダイアログを開く"""
        if self.is_folder:
            self.file_picker_element.get_directory_path(
                dialog_title="フォルダを選択",
                initial_directory=self.directory if self.directory else None,
            )
        else:
            self.file_picker_element.pick_files(
                allowed_extensions=self.allowed_extensions,
                dialog_title="ファイルを選択",
                initial_directory=self.directory if self.directory else None,
            )

    def get_selected_file(self) -> Optional[str]:
        """選択されたファイルパスを取得する"""
        return self.selected_file

    def get_selected_folder(self) -> Optional[str]:
        """選択されたフォルダパスを取得する"""
        return self.selected_folder

    def get_selected_item(self) -> Optional[str]:
        """選択されたアイテム（ファイルまたはフォルダ）のパスを取得する"""
        return self.selected_file if not self.is_folder else self.selected_folder

    def get_file_picker_overlay(self) -> ft.FilePicker:
        """ファイルピッカーのオーバーレイを取得する"""
        return self.file_picker_element

    def set_selected_file(self, file_path: str) -> None:
        """選択されたファイルを設定する"""
        try:
            if not self._validate_file_extension(file_path):
                raise FilePickerError(
                    f"サポートされていないファイル形式です: {Path(file_path).suffix}"
                )

            self.selected_file = file_path
            self.selected_folder = None
            self.label_text_element.value = (
                f"選択されたファイル: {Path(file_path).name}"
            )
            self.label_text_element.color = ft.Colors.GREY_600

            if self._on_change:
                self._on_change(file_path)

            self.update()

        except Exception as e:
            print(f"ファイル設定エラー: {e}")

    def set_selected_folder(self, folder_path: str) -> None:
        """選択されたフォルダを設定する"""
        try:
            if not Path(folder_path).is_dir():
                raise FilePickerError(
                    f"指定されたパスはフォルダではありません: {folder_path}"
                )

            self.selected_folder = folder_path
            self.selected_file = None
            self.label_text_element.value = (
                f"選択されたフォルダ: {Path(folder_path).name}"
            )
            self.label_text_element.color = ft.Colors.GREY_600

            if self._on_change:
                self._on_change(folder_path)

            self.update()

        except Exception as e:
            print(f"フォルダ設定エラー: {e}")

    def clear_selection(self) -> None:
        """選択をクリアする"""
        self.selected_file = None
        self.selected_folder = None
        self.label_text_element.value = "選択されていません"
        self.label_text_element.color = ft.Colors.GREY_600
        self.update()

    def is_file_selected(self) -> bool:
        """ファイルが選択されているかどうかを確認する"""
        return self.selected_file is not None

    def is_folder_selected(self) -> bool:
        """フォルダが選択されているかどうかを確認する"""
        return self.selected_folder is not None

    def is_item_selected(self) -> bool:
        """アイテム（ファイルまたはフォルダ）が選択されているかどうかを確認する"""
        return self.get_selected_item() is not None


if __name__ == "__main__":

    def on_file_selected(file_path: str) -> None:
        print(f"Selected file: {file_path}")

    def on_folder_selected(folder_path: str) -> None:
        print(f"Selected folder: {folder_path}")

    def main(page: ft.Page):
        page.title = "FilePicker Component Test"

        file_picker = FilePicker(
            is_folder=False, directory="", on_change=on_file_selected
        )

        folder_picker = FilePicker(
            is_folder=True, directory="", on_change=on_folder_selected
        )

        page.add(
            ft.Text("ファイル選択:", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
            file_picker,
            ft.Text("フォルダ選択:", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
            folder_picker,
        )

        page.overlay.extend(
            [
                file_picker.get_file_picker_overlay(),
                folder_picker.get_file_picker_overlay(),
            ]
        )

        page.update()

    ft.app(target=main)
