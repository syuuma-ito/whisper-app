import logging
from pathlib import Path
from typing import Any, Dict, Generator, List

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    pass


class WhisperTranscriber:
    """Whisperを使用した文字起こしクラス"""

    def __init__(self, model: str, compute_type: str, device: str):
        self.model_name = model
        self.compute_type = compute_type
        self.device = self._normalize_device(device)
        self.whisper_model = None

    def _normalize_device(self, device: str) -> str:
        """デバイス名を正規化する"""
        device_map = {"GPU": "cuda", "CPU": "cpu", "cuda": "cuda", "cpu": "cpu"}

        normalized_device = device_map.get(device.upper())
        if normalized_device is None:
            raise ValueError(f"無効なデバイス: {device}")

        return normalized_device

    def _validate_file_path(self, file_path: str) -> Path:
        """ファイルパスを検証する"""
        path = Path(file_path)

        if not path.exists():
            raise TranscriptionError(f"ファイルが見つかりません: {file_path}")

        if not path.is_file():
            raise TranscriptionError(
                f"指定されたパスはファイルではありません: {file_path}"
            )

        supported_extensions = {".mp3", ".wav", ".m4a", ".mp4", ".mov", ".avi", ".mkv"}
        if path.suffix.lower() not in supported_extensions:
            raise TranscriptionError(
                f"サポートされていないファイル形式です: {path.suffix}"
            )

        return path

    def _validate_output_folder(self, output_folder: str) -> Path:
        """出力フォルダを検証する"""
        path = Path(output_folder)

        if not path.exists():
            raise TranscriptionError(f"出力フォルダが見つかりません: {output_folder}")

        if not path.is_dir():
            raise TranscriptionError(
                f"指定されたパスはフォルダではありません: {output_folder}"
            )

        return path

    def _load_model(self) -> None:
        """Whisperモデルを読み込む"""
        try:
            self.whisper_model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
        except Exception as e:
            raise TranscriptionError(f"モデルの読み込みに失敗しました: {e}")

    def _transcribe_audio(self, input_file_path: Path):
        """音声ファイルを文字起こしする"""
        if self.whisper_model is None:
            self._load_model()
        if self.whisper_model is None:
            raise TranscriptionError("Whisperモデルが初期化されていません")

        try:
            segments, info = self.whisper_model.transcribe(
                str(input_file_path),
                beam_size=5,
            )
        except Exception as e:
            raise TranscriptionError(f"文字起こしの実行に失敗しました: {e}")

        audio_length = info.duration

        yield {
            "message": f"言語: {info.language} (確率: {info.language_probability:.2f})",
            "level": "INFO",
            "progress": 0,
            "label": "文字起こし中...",
        }
        yield {
            "message": f"音声の長さ: {audio_length:.2f}秒",
            "level": "DEBUG",
            "progress": 0,
            "label": "文字起こし中...",
        }

        result = []
        for segment in segments:
            yield {
                "message": f"[{segment.start:.2f} -> {segment.end:.2f}] {segment.text.strip()}",
                "level": "DEBUG",
                "progress": min(segment.start / audio_length, 1.0),
                "label": "文字起こし中...",
            }
            result.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                }
            )

        return result

    def _save_transcription(
        self, result: List[Dict[str, Any]], output_path: Path
    ) -> None:
        """文字起こし結果をファイルに保存する"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for item in result:
                    f.write(
                        f"[{item['start']:.2f}s -> {item['end']:.2f}s] {item['text']}\n"
                    )
        except Exception as e:
            raise TranscriptionError(f"ファイルの保存に失敗しました: {e}")

    def transcribe(
        self, input_file: str, output_folder: str
    ) -> Generator[Dict[str, Any], None, None]:
        """文字起こしを実行する"""
        yield {
            "message": "文字起こしを開始します。",
            "level": "INFO",
            "progress": 0.0,
            "label": "文字起こしを開始しています...",
        }

        yield {
            "message": f"モデル: {self.model_name}, 精度: {self.compute_type}, デバイス: {self.device}",
            "level": "DEBUG",
            "label": "文字起こしを開始しています...",
            "progress": 0.0,
        }

        yield {
            "message": "モデルの読み込み中...(初回は時間がかかる場合があります)",
            "level": "INFO",
            "label": "文字起こしを開始しています...",
            "progress": 0,
        }

        input_file_path = self._validate_file_path(input_file)
        output_folder_path = self._validate_output_folder(output_folder)

        self._load_model()

        yield {
            "message": "モデルの読み込みが完了しました。",
            "level": "INFO",
            "label": "文字起こしを開始しています...",
            "progress": 0.0,
        }

        result = []
        for update in self._transcribe_audio(input_file_path):
            result.append(update)
            yield update

        output_file_path = (
            output_folder_path / f"{input_file_path.stem}_transcription.txt"
        )

        yield {
            "message": f"出力ファイル: {output_file_path}",
            "level": "INFO",
            "progress": 1.0,
            "label": "ファイルを保存中...",
        }

        transcription_result = [item for item in result if "start" in item]
        self._save_transcription(transcription_result, output_file_path)

        yield {
            "message": "文字起こしが完了しました",
            "level": "INFO",
            "progress": 1.0,
            "label": "文字起こしを完了しました。",
        }


def transcription(
    settings: Dict[str, Any],
    input_file: str,
    output_folder: str,
    logger,
    progress_bar,
    disabled_start_button,
) -> None:
    """文字起こしを実行する関数"""
    try:
        disabled_start_button(True)

        required_keys = ["model", "compute_type", "device"]
        for key in required_keys:
            if key not in settings:
                raise TranscriptionError(f"必要な設定が不足しています: {key}")

        transcriber = WhisperTranscriber(
            model=settings["model"],
            compute_type=settings["compute_type"],
            device=settings["device"],
        )

        logger.info("文字起こしを開始します。")
        logger.debug(f"設定: {settings}")
        logger.debug(f"入力ファイル: {input_file}")
        logger.debug(f"出力フォルダ: {output_folder}")

        for update in transcriber.transcribe(input_file, output_folder):
            logger.add_log(update["message"], update["level"])
            progress_bar.update_value(update["progress"], update["label"])

    except TranscriptionError as e:
        logger.error(f"文字起こしエラー: {e}")
        progress_bar.update_value(0, "エラーが発生しました")
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        progress_bar.update_value(0, "エラーが発生しました")
    finally:
        disabled_start_button(False)
