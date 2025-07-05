from typing import Any, Callable, Dict, Optional

import flet as ft
from utils.language_codes import validate_language_code
from utils.torch import can_use_gpu


class Settings(ft.Container):
    """文字起こし設定を管理するコンポーネント"""

    # 有効な言語コードのリスト

    def __init__(
        self,
        settings: Optional[Dict[str, Any]] = None,
        on_change: Optional[Callable] = None,
    ):
        super().__init__()
        self.padding = 10

        self._on_change = on_change
        self.gpu_available = can_use_gpu()

        self.transcription_settings = self._get_default_settings(settings)

        self._setup_ui_components()
        self._setup_layout()

        self._set_initial_visibility()

    def _get_default_settings(
        self, settings: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """デフォルト設定を取得する"""
        default_settings = {
            "model": "large-v3-turbo",
            "compute_type": "float32",
            "device": "CPU",
            "language": "auto",  # デフォルトは自動検出
        }

        if settings:
            default_settings.update(settings)

        if not self.gpu_available and default_settings["device"] == "GPU":
            default_settings["device"] = "CPU"

        return default_settings

    def _setup_ui_components(self) -> None:
        """UIコンポーネントを初期化する"""
        self.device_select_element = ft.Dropdown(
            options=[
                ft.dropdown.Option("CPU"),
                ft.dropdown.Option("GPU", disabled=not self.gpu_available),
            ],
            label="デバイス",
            value=self.transcription_settings["device"],
            on_change=self._on_device_change,
            color=ft.Colors.BLUE_600 if self.gpu_available else ft.Colors.GREY_400,
        )

        self.model_select_element = ft.Dropdown(
            options=[
                ft.dropdown.Option("tiny"),
                ft.dropdown.Option("base"),
                ft.dropdown.Option("small"),
                ft.dropdown.Option("medium"),
                ft.dropdown.Option("large-v3-turbo"),
            ],
            label="モデル",
            value=self.transcription_settings["model"],
            on_change=self._on_model_change,
        )

        self.compute_type_cpu_select_element = ft.Dropdown(
            options=[
                ft.dropdown.Option("int8"),
                ft.dropdown.Option("float32"),
            ],
            label="精度(CPU)",
            value=self.transcription_settings["compute_type"],
            on_change=self._on_compute_type_change,
        )

        self.compute_type_gpu_select_element = ft.Dropdown(
            options=[
                ft.dropdown.Option("int8"),
                ft.dropdown.Option("int8_float16"),
                ft.dropdown.Option("float16"),
                ft.dropdown.Option("float32"),
            ],
            label="精度(GPU)",
            value=self.transcription_settings["compute_type"],
            on_change=self._on_compute_type_change,
            color=ft.Colors.BLUE_600 if self.gpu_available else ft.Colors.GREY_400,
            disabled=not self.gpu_available,
        )

        # 言語選択コンポーネントを追加
        self.language_select_element = ft.Dropdown(
            options=[
                ft.dropdown.Option("auto", "自動検出"),
                ft.dropdown.Option("ja", "日本語"),
                ft.dropdown.Option("en", "英語"),
                ft.dropdown.Option("other", "その他"),
            ],
            label="言語",
            value=self.transcription_settings["language"],
            on_change=self._on_language_change,
            width=150,
        )

        # カスタム言語コード入力フィールド
        self.custom_language_input = ft.TextField(
            label="言語コード",
            hint_text="例: fr, de, es",
            value="ja",  # デフォルトは"ja"
            on_change=self._on_custom_language_change,
            width=150,
            visible=False,  # 初期状態では非表示
        )

        # エラーメッセージ表示用
        self.language_error_text = ft.Text(
            "無効な言語コードです",
            color=ft.Colors.RED,
            size=12,
            visible=False,
        )

    def _setup_layout(self) -> None:
        """レイアウトを設定する"""
        self.content = ft.Column(
            [
                self.device_select_element,
                ft.Row(
                    [
                        self.model_select_element,
                        self.compute_type_cpu_select_element,
                        self.compute_type_gpu_select_element,
                    ]
                ),
                ft.Row(
                    [
                        self.language_select_element,
                        self.custom_language_input,
                        self.language_error_text,
                    ]
                ),
            ]
        )

    def _set_initial_visibility(self) -> None:
        """初期表示状態を設定する（update()は呼ばない）"""
        device = self.transcription_settings["device"]

        if device == "CPU":
            self.compute_type_cpu_select_element.visible = True
            self.compute_type_gpu_select_element.visible = False
        else:
            self.compute_type_cpu_select_element.visible = False
            self.compute_type_gpu_select_element.visible = True

        # 言語設定の初期表示状態を設定
        language = self.transcription_settings["language"]
        if language == "auto":
            self.language_select_element.value = "auto"
            self.custom_language_input.value = "ja"
        elif language == "ja":
            self.language_select_element.value = "ja"
            self.custom_language_input.value = "ja"
        elif language == "en":
            self.language_select_element.value = "en"
            self.custom_language_input.value = "en"
        else:
            # カスタム言語コードの場合
            self.language_select_element.value = "other"
            self.custom_language_input.value = language

        self._update_language_input_visibility()

    def _update_compute_type_visibility(self) -> None:
        """デバイス設定に応じてcompute_typeドロップダウンの表示を切り替える"""
        device = self.transcription_settings["device"]

        if device == "CPU":
            self.compute_type_cpu_select_element.visible = True
            self.compute_type_gpu_select_element.visible = False
        else:
            self.compute_type_cpu_select_element.visible = False
            self.compute_type_gpu_select_element.visible = True

        if hasattr(self, "page") and self.page:
            self.update()

    def _on_device_change(self, e: ft.ControlEvent) -> None:
        """デバイス選択の変更ハンドラー"""
        if e.control.value == "GPU" and not self.gpu_available:
            e.control.value = "CPU"
            return

        self.transcription_settings["device"] = e.control.value
        self._update_compute_type_visibility()

        if self._on_change:
            self._on_change(self.transcription_settings)

    def _on_model_change(self, e: ft.ControlEvent) -> None:
        """モデル選択の変更ハンドラー"""
        self.transcription_settings["model"] = e.control.value
        if self._on_change:
            self._on_change(self.transcription_settings)

    def _on_compute_type_change(self, e: ft.ControlEvent) -> None:
        """精度選択の変更ハンドラー"""
        self.transcription_settings["compute_type"] = e.control.value
        if self._on_change:
            self._on_change(self.transcription_settings)

    def _on_language_change(self, e: ft.ControlEvent) -> None:
        """言語選択の変更ハンドラー"""
        language = e.control.value

        if language == "auto":
            self.transcription_settings["language"] = "auto"
            self.language_error_text.visible = False
            self.language_error_text.value = ""
        elif language == "ja":
            self.transcription_settings["language"] = "ja"
            self.language_error_text.visible = False
            self.language_error_text.value = ""
        elif language == "en":
            self.transcription_settings["language"] = "en"
            self.language_error_text.visible = False
            self.language_error_text.value = ""
        elif language == "other":
            # その他の場合は、テキストボックスの値を検証して使用
            custom_value = (
                self.custom_language_input.value.strip()
                if self.custom_language_input.value
                else ""
            )
            if custom_value and validate_language_code(custom_value):
                self.transcription_settings["language"] = custom_value
                self.language_error_text.visible = False
                self.language_error_text.value = ""
            elif custom_value:
                # 無効な言語コードの場合
                self.transcription_settings["language"] = ""
                self.language_error_text.visible = True
                self.language_error_text.value = "無効な言語コードです"
            else:
                # 空の場合
                self.transcription_settings["language"] = ""
                self.language_error_text.visible = False
                self.language_error_text.value = ""

        self._update_language_input_visibility()

        # UIを更新
        if hasattr(self, "page") and self.page:
            self.update()

        if self._on_change:
            self._on_change(self.transcription_settings)

    def _on_custom_language_change(self, e: ft.ControlEvent) -> None:
        """カスタム言語コード入力の変更ハンドラー"""
        custom_language = e.control.value.strip() if e.control.value else ""

        # リアルタイムで言語コードの妥当性をチェック
        if custom_language:
            if validate_language_code(custom_language):
                self.transcription_settings["language"] = custom_language
                self.language_error_text.visible = False
                self.language_error_text.value = ""
            else:
                self.transcription_settings["language"] = ""
                self.language_error_text.visible = True
                self.language_error_text.value = "無効な言語コードです"
        else:
            # 空の場合
            self.transcription_settings["language"] = ""
            self.language_error_text.visible = False
            self.language_error_text.value = ""

        # UIを更新
        if hasattr(self, "page") and self.page:
            self.update()

        if self._on_change:
            self._on_change(self.transcription_settings)

    def get_transcription_settings(self) -> Dict[str, Any]:
        """現在の文字起こし設定を返す"""
        return self.transcription_settings.copy()

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """設定を更新する"""
        self.transcription_settings.update(new_settings)

        if "device" in new_settings:
            self.device_select_element.value = new_settings["device"]
            self._update_compute_type_visibility()

        if "model" in new_settings:
            self.model_select_element.value = new_settings["model"]

        if "compute_type" in new_settings:
            self.compute_type_cpu_select_element.value = new_settings["compute_type"]
            self.compute_type_gpu_select_element.value = new_settings["compute_type"]

        if "language" in new_settings:
            language = new_settings["language"]
            if language == "auto":
                self.language_select_element.value = "auto"
                self.custom_language_input.value = "ja"
            elif language == "ja":
                self.language_select_element.value = "ja"
                self.custom_language_input.value = "ja"
            elif language == "en":
                self.language_select_element.value = "en"
                self.custom_language_input.value = "en"
            else:
                # カスタム言語コードの場合
                self.language_select_element.value = "other"
                self.custom_language_input.value = language
                # バリデーション
                if validate_language_code(language):
                    self.language_error_text.visible = False
                else:
                    self.language_error_text.visible = True

            self._update_language_input_visibility()

        if hasattr(self, "page") and self.page:
            self.update()

    def _update_language_input_visibility(self) -> None:
        """言語設定に応じてカスタム言語入力フィールドの表示を切り替える"""
        language = self.language_select_element.value

        if language == "other":
            self.custom_language_input.visible = True
        else:
            self.custom_language_input.visible = False
            self.language_error_text.visible = False  # エラーメッセージも非表示

        if hasattr(self, "page") and self.page:
            self.update()


if __name__ == "__main__":

    def on_settings_change(settings: Dict[str, Any]) -> None:
        print("Settings changed:", settings)

    def main(page: ft.Page):
        page.title = "Settings Component Test"

        initial_settings = {
            "model": "medium",
            "compute_type": "int8",
            "device": "CPU",
            "language": "auto",
        }

        settings_component = Settings(
            on_change=on_settings_change, settings=initial_settings
        )
        page.add(settings_component)

    ft.app(target=main)
