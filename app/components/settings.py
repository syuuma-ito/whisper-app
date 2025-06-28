from typing import Any, Callable, Dict, Optional

import flet as ft
from utils.torch import can_use_gpu


class Settings(ft.Container):
    """文字起こし設定を管理するコンポーネント"""

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
            "model": "medium",
            "compute_type": "int8",
            "device": "CPU",
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
        }

        settings_component = Settings(
            on_change=on_settings_change, settings=initial_settings
        )
        page.add(settings_component)

    ft.app(target=main)
