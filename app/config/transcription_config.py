from typing import Any, Dict, List, Optional

from utils.language_codes import validate_language_code
from utils.torch import can_use_gpu

AVAILABLE_MODELS = [
    "base",
    "small",
    "medium",
    "large-v3",
    "large-v3-turbo",
    "distil-large-v3",
]
AVAILABLE_COMPUTE_TYPES = [
    "int8",
    "float16",
    "float32",
]


class TranscriptionConfig:
    """文字起こし設定を管理するクラス"""

    def __init__(
        self,
        model: str = "large-v3-turbo",
        compute_type: str = "float32",
        device: str = "CPU",
        language: str = "auto",
    ):
        self.model = model
        self.compute_type = compute_type
        self.device = device
        self.language = language

        self.AVAILABLE_MODELS: List[str] = AVAILABLE_MODELS
        self.AVAILABLE_COMPUTE_TYPES: List[str] = AVAILABLE_COMPUTE_TYPES

    @classmethod
    def from_dict(cls, settings: Dict[str, Any]) -> "TranscriptionConfig":
        """辞書から設定オブジェクトを作成する"""
        return cls(
            model=settings["model"],
            compute_type=settings["compute_type"],
            device=settings["device"],
            language=settings["language"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す"""
        return {
            "model": self.model,
            "compute_type": self.compute_type,
            "device": self.device,
            "language": self.language,
        }

    @classmethod
    def get_default_settings(cls) -> "TranscriptionConfig":
        """デフォルト設定を取得する"""
        return cls(
            model="large-v3-turbo",
            compute_type="float16" if can_use_gpu() else "float32",
            device="GPU" if can_use_gpu() else "CPU",
            language="auto",
        )

    def is_valid_language(self) -> bool:
        """言語設定が有効かどうかを確認する"""
        if self.language == "auto" or self.language == "":
            return self.language != ""

        return validate_language_code(self.language)
