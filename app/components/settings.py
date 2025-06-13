import flet as ft
from utils.torch import can_use_gpu


class Settings(ft.Container):
    def __init__(self, settings: dict = None, on_change=None):
        super().__init__()
        self.padding = 10

        self._on_change = on_change
        self.gpu_available = can_use_gpu()

        self.transcription_settings = settings or {
            "model": "medium",
            "compute_type": "int8",
            "device": (
                "CPU" if not self.gpu_available else settings.get("device", "CPU")
            ),
        }

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

        # GPUが使用できない場合は強制的にCPUに設定
        if not self.gpu_available and self.transcription_settings["device"] == "GPU":
            self.transcription_settings["device"] = "CPU"
            self.device_select_element.value = "CPU"

        device = self.transcription_settings["device"]
        if device == "CPU":
            self.compute_type_cpu_select_element.visible = True
            self.compute_type_gpu_select_element.visible = False
        else:  # GPU
            self.compute_type_cpu_select_element.visible = False
            self.compute_type_gpu_select_element.visible = True

    def update_compute_type_visibility(self):
        """デバイス設定に応じてcompute_typeドロップダウンの表示を切り替える"""
        device = self.transcription_settings["device"]
        if device == "CPU":
            self.compute_type_cpu_select_element.visible = True
            self.compute_type_gpu_select_element.visible = False
        else:  # GPU
            self.compute_type_cpu_select_element.visible = False
            self.compute_type_gpu_select_element.visible = True

        self.update()

    def _on_device_change(self, e: ft.ControlEvent):
        """デバイス選択の変更ハンドラー"""
        # GPUが使用できない場合はGPU選択を無視
        if e.control.value == "GPU" and not self.gpu_available:
            e.control.value = "CPU"
            return

        self.transcription_settings["device"] = e.control.value
        self.update_compute_type_visibility()
        if self._on_change:
            self._on_change(self.transcription_settings)

    def _on_model_change(self, e: ft.ControlEvent):
        """モデル選択の変更ハンドラー"""
        self.transcription_settings["model"] = e.control.value
        if self._on_change:
            self._on_change(self.transcription_settings)

    def _on_compute_type_change(self, e: ft.ControlEvent):
        """精度選択の変更ハンドラー"""
        self.transcription_settings["compute_type"] = e.control.value
        if self._on_change:
            self._on_change(self.transcription_settings)

    def get_transcription_settings(self):
        """現在の文字起こし設定を返す"""
        return self.transcription_settings


if __name__ == "__main__":
    # テスト用の簡易アプリケーション
    def on_settings_change(settings):
        print("Settings changed:", settings)

    def main(page: ft.Page):
        settings = {
            "model": "medium",
            "compute_type": "int8",
            "device": "CPU",
        }
        page.title = "Settings Component Test"
        settings = Settings(on_change=on_settings_change, settings=settings)
        page.add(settings)

    ft.app(target=main)
