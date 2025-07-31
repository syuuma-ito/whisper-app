import logging
import queue
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    pass


class WhisperTranscriber:
    """Whisperを使用した文字起こしクラス"""

    def __init__(
        self, model: str, compute_type: str, device: str, language: str = "auto"
    ):
        self.model_name = model
        self.compute_type = compute_type
        self.device = self._normalize_device(device)
        self.language = self._normalize_language(language)
        self.whisper_model = None

    def _normalize_device(self, device: str) -> str:
        """デバイス名を正規化する"""
        device_map = {"GPU": "cuda", "CPU": "cpu", "cuda": "cuda", "cpu": "cpu"}

        normalized_device = device_map.get(device.upper())
        if normalized_device is None:
            raise ValueError(f"無効なデバイス: {device}")

        return normalized_device

    def _normalize_language(self, language: str) -> Optional[str]:
        """言語設定を正規化する"""
        if not language or language == "auto":
            return None  # 自動検出
        return language.lower().strip()

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

    def _transcribe_audio(self, input_file_path: Path, should_stop_callback=None):
        """音声ファイルを文字起こしする"""
        if self.whisper_model is None:
            self._load_model()
        if self.whisper_model is None:
            raise TranscriptionError("Whisperモデルが初期化されていません")

        try:
            segments, info = self.whisper_model.transcribe(
                str(input_file_path),
                language=self.language,
            )
        except Exception as e:
            raise TranscriptionError(f"文字起こしの実行に失敗しました: {e}")

        audio_length = info.duration

        yield {
            "message": f"言語: {info.language}",
            "level": "INFO",
            "progress": 0,
        }
        yield {
            "message": f"音声の長さ: {audio_length:.2f}秒",
            "level": "DEBUG",
            "progress": 0,
        }

        result = []
        for segment in segments:
            if should_stop_callback and should_stop_callback():
                return result

            yield {
                "message": f"[{segment.start:.2f} -> {segment.end:.2f}] {segment.text.strip()}",
                "level": "DEBUG",
                "progress": min(segment.start / audio_length, 1.0),
                "result": {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                },
            }

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
        self, input_file: str, output_folder: str, should_stop_callback=None
    ) -> Generator[Dict[str, Any], None, None]:
        """文字起こしを実行する"""
        yield {
            "message": "モデルの読み込み中...(初回は時間がかかる場合があります)",
            "level": "INFO",
            "progress": 0,
        }

        input_file_path = self._validate_file_path(input_file)
        output_folder_path = self._validate_output_folder(output_folder)

        if should_stop_callback and should_stop_callback():
            return

        self._load_model()

        if should_stop_callback and should_stop_callback():
            return

        yield {
            "message": "モデルの読み込みが完了しました。",
            "level": "INFO",
            "progress": 0.0,
        }

        result = []
        for update in self._transcribe_audio(input_file_path, should_stop_callback):
            if should_stop_callback and should_stop_callback():
                return

            yield update

            if "result" in update:
                result.append(update["result"])

        output_file_path = (
            output_folder_path / f"{input_file_path.stem}_transcription.txt"
        )

        yield {
            "message": f"出力ファイル: {output_file_path}",
            "level": "INFO",
            "progress": 1.0,
        }

        self._save_transcription(result, output_file_path)

        yield {
            "message": "文字起こしが完了しました",
            "level": "INFO",
            "progress": 1.0,
        }


def transcription(
    settings: Dict[str, Any],
    input_file: str,
    output_folder: str,
    message_queue: queue.Queue,
    should_stop_callback,
) -> None:
    """文字起こしを実行する関数"""
    try:
        message_queue.put({"type": "transcription_started"})

        required_keys = ["model", "compute_type", "device"]
        for key in required_keys:
            if key not in settings:
                raise TranscriptionError(f"必要な設定が不足しています: {key}")

        transcriber = WhisperTranscriber(
            model=settings["model"],
            compute_type=settings["compute_type"],
            device=settings["device"],
            language=settings.get("language", "auto"),
        )

        message_queue.put(
            {"type": "log", "text": "文字起こしを開始します。", "level": "INFO"}
        )

        message_queue.put({"type": "log", "text": f"設定:", "level": "DEBUG"})
        for key, value in settings.items():
            message_queue.put(
                {"type": "log", "text": f"- {key}: {value}", "level": "DEBUG"}
            )

        message_queue.put(
            {"type": "log", "text": f"入力ファイル: {input_file}", "level": "DEBUG"}
        )

        message_queue.put(
            {"type": "log", "text": f"出力フォルダ: {output_folder}", "level": "DEBUG"}
        )

        transcription_completed = False
        for update in transcriber.transcribe(
            input_file, output_folder, should_stop_callback
        ):
            if should_stop_callback():
                message_queue.put(
                    {
                        "type": "log",
                        "text": "文字起こしが停止されました",
                        "level": "WARNING",
                    }
                )
                message_queue.put({"type": "progress", "value": 0})
                message_queue.put({"type": "transcription_stopped"})
                return

            message_queue.put(
                {"type": "log", "text": update["message"], "level": update["level"]}
            )

            message_queue.put(
                {
                    "type": "progress",
                    "value": update["progress"],
                }
            )

            if update.get(
                "progress"
            ) == 1.0 and "文字起こしが完了しました" in update.get("message", ""):
                transcription_completed = True

        if not transcription_completed:
            message_queue.put(
                {
                    "type": "log",
                    "text": "文字起こしが停止されました",
                    "level": "WARNING",
                }
            )
            message_queue.put({"type": "progress", "value": 0})
            message_queue.put({"type": "transcription_stopped"})
            return

        message_queue.put({"type": "transcription_finished"})

    except TranscriptionError as e:
        message_queue.put({"type": "error", "text": f"文字起こしエラー: {e}"})
        message_queue.put({"type": "progress", "value": 0})
        return
    except Exception as e:
        message_queue.put(
            {"type": "error", "text": f"予期しないエラーが発生しました: {e}"}
        )
        message_queue.put({"type": "progress", "value": 0})
        return
