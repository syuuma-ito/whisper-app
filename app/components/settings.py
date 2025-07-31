from typing import Any, Callable, Dict, Optional

import flet as ft
from config.transcription_config import TranscriptionConfig
from utils.language_codes import validate_language_code
from utils.torch import can_use_gpu


class Settings(ft.Container):
    """文字起こし設定を管理するコンポーネント"""

    LANGUAGE_OPTIONS = [
        ft.dropdown.Option("auto", "自動検出"),
        ft.dropdown.Option("ja", "日本語"),
        ft.dropdown.Option("en", "英語"),
        ft.dropdown.Option("other", "その他"),
    ]

    PREDEFINED_LANGUAGES = {"auto", "ja", "en"}
    ERROR_MESSAGE = "無効な言語コードです"

    def __init__(
        self,
        settings: Optional[Dict[str, Any]] = None,
        on_change: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        super().__init__()
        self.padding = 10

        self._on_change = on_change
        self.gpu_available = can_use_gpu()
        self.config = TranscriptionConfig()

        self.transcription_settings = self._get_default_settings(settings)

        self._setup_ui_components()
        self._setup_layout()

    def _get_default_settings(
        self, settings: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """デフォルト設定を取得する"""
        if settings:
            config = TranscriptionConfig.from_dict(settings)
        else:
            config = TranscriptionConfig.get_default_settings()

        return config.to_dict()

    def _setup_ui_components(self) -> None:
        """UIコンポーネントを初期化する"""
        self._create_device_dropdown()
        self._create_model_dropdown()
        self._create_compute_type_dropdown()
        self._create_language_components()

    def _create_device_dropdown(self) -> None:
        """デバイス選択ドロップダウンを作成する"""
        self.device_select_element = ft.Dropdown(
            options=[
                ft.dropdown.Option("CPU"),
                ft.dropdown.Option("GPU", disabled=not self.gpu_available),
            ],
            label="デバイス",
            value=self.transcription_settings["device"],
            on_change=self._on_device_change,
            color=self._get_device_color(),
        )

    def _create_model_dropdown(self) -> None:
        """モデル選択ドロップダウンを作成する"""
        model_options = [
            ft.dropdown.Option(model) for model in self.config.AVAILABLE_MODELS
        ]
        self.model_select_element = ft.Dropdown(
            options=model_options,
            label="モデル",
            value=self.transcription_settings["model"],
            on_change=self._on_model_change,
        )

    def _create_compute_type_dropdown(self) -> None:
        """精度選択ドロップダウンを作成する"""
        compute_type_options = [
            ft.dropdown.Option(ct) for ct in self.config.AVAILABLE_COMPUTE_TYPES
        ]
        self.compute_type_select_element = ft.Dropdown(
            options=compute_type_options,
            label="精度",
            value=self.transcription_settings["compute_type"],
            on_change=self._on_compute_type_change,
        )

    def _create_language_components(self) -> None:
        """言語選択関連のコンポーネントを作成する"""
        self.language_select_element = ft.Dropdown(
            options=self.LANGUAGE_OPTIONS,
            label="言語",
            value=self.transcription_settings["language"],
            on_change=self._on_language_change,
            width=150,
        )

        self.custom_language_input = ft.TextField(
            label="言語コード",
            hint_text="例: fr, de, es",
            value="",
            on_change=self._on_custom_language_change,
            width=150,
            visible=False,
        )

        self.language_error_text = ft.Text(
            self.ERROR_MESSAGE,
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
                        self.compute_type_select_element,
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

    def _get_device_color(self) -> str:
        """デバイス選択の色を取得する"""
        current_device = self.transcription_settings.get("device", "CPU")
        return (
            ft.Colors.BLUE_600
            if current_device == "GPU" and self.gpu_available
            else None
        )

    def _on_device_change(self, e: ft.ControlEvent) -> None:
        """デバイス選択の変更ハンドラー"""
        if e.control.value == "GPU" and not self.gpu_available:
            e.control.value = "CPU"
            return

        self._update_setting("device", e.control.value)

        # デバイス変更時に色も更新
        self.device_select_element.color = self._get_device_color()
        self._refresh_ui()

    def _on_model_change(self, e: ft.ControlEvent) -> None:
        """モデル選択の変更ハンドラー"""
        self._update_setting("model", e.control.value)

    def _on_compute_type_change(self, e: ft.ControlEvent) -> None:
        """精度選択の変更ハンドラー"""
        self._update_setting("compute_type", e.control.value)

    def _update_setting(self, key: str, value: Any) -> None:
        """設定を更新して変更通知を送る"""
        self.transcription_settings[key] = value
        if self._on_change:
            self._on_change(self.transcription_settings)

    def _on_language_change(self, e: ft.ControlEvent) -> None:
        """言語選択の変更ハンドラー"""
        language = e.control.value

        if language in self.PREDEFINED_LANGUAGES:
            self._handle_predefined_language(language)
        elif language == "other":
            self._handle_custom_language()

        self._update_language_input_visibility()
        self._refresh_ui()

        if self._on_change:
            self._on_change(self.transcription_settings)

    def _handle_predefined_language(self, language: str) -> None:
        """定義済み言語の処理"""
        self.transcription_settings["language"] = language
        self._clear_language_error()

    def _handle_custom_language(self) -> None:
        """カスタム言語の処理"""
        custom_value = self._get_custom_language_value()

        if not custom_value:
            self.transcription_settings["language"] = ""
            self._clear_language_error()
        elif validate_language_code(custom_value):
            self.transcription_settings["language"] = custom_value
            self._clear_language_error()
        else:
            self.transcription_settings["language"] = ""
            self._show_language_error()

    def _get_custom_language_value(self) -> str:
        """カスタム言語の値を取得する"""
        return (
            self.custom_language_input.value.strip()
            if self.custom_language_input.value
            else ""
        )

    def _clear_language_error(self) -> None:
        """言語エラーをクリアする"""
        self.language_error_text.visible = False
        self.language_error_text.value = ""

    def _show_language_error(self) -> None:
        """言語エラーを表示する"""
        self.language_error_text.visible = True
        self.language_error_text.value = self.ERROR_MESSAGE

    def _refresh_ui(self) -> None:
        """UIを更新する"""
        self.update()

    def _on_custom_language_change(self, e: ft.ControlEvent) -> None:
        """カスタム言語コード入力の変更ハンドラー"""
        custom_language = e.control.value.strip() if e.control.value else ""

        self._validate_and_update_custom_language(custom_language)
        self._refresh_ui()

        if self._on_change:
            self._on_change(self.transcription_settings)

    def _validate_and_update_custom_language(self, custom_language: str) -> None:
        """カスタム言語コードの妥当性をチェックして更新する"""
        if not custom_language:
            self.transcription_settings["language"] = ""
            self._clear_language_error()
        elif validate_language_code(custom_language):
            self.transcription_settings["language"] = custom_language
            self._clear_language_error()
        else:
            self.transcription_settings["language"] = ""
            self._show_language_error()

    def _update_language_input_visibility(self) -> None:
        """言語設定に応じてカスタム言語入力フィールドの表示を切り替える"""
        is_custom_language = self.language_select_element.value == "other"

        self.custom_language_input.visible = is_custom_language

        if not is_custom_language:
            self._clear_language_error()

        self._refresh_ui()
