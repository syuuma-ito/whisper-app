from faster_whisper import WhisperModel
from pathlib import Path


def _run_whisper(
    model,
    compute_type,
    device,
    input_file,
    output_folder,
):
    """
    Whisperを使用して文字起こしを実行する関数。
    """
    if device == "GPU":
        device = "cuda"
    elif device == "CPU":
        device = "cpu"
    else:
        raise ValueError(f"無効なデバイス: {device}")

    input_file_path = Path(input_file)

    yield {
        "message": "文字起こしを開始します。",
        "level": "INFO",
        "progress": 0.0,
        "label": "文字起こしを開始しています...",
    }
    yield {
        "message": f"モデル: {model}, 精度: {compute_type}, デバイス: {device}",
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

    model = WhisperModel(
        model,
        device=device,
        compute_type=compute_type,
    )

    yield {
        "message": "モデルの読み込みが完了しました。",
        "level": "INFO",
        "label": "文字起こしを開始しています...",
        "progress": 0.0,
    }

    segments, info = model.transcribe(
        input_file_path,
        beam_size=5,
    )
    audio_length = info.duration

    yield {
        "message": f"言語: {info.language} (確率: {info.language_probability:.2f})",
        "level": "INFO",
        "progress": 0,
        "label": "文字起こしを開始しています...",
    }
    yield {
        "message": f"音声の長さ: {audio_length:.2f}秒",
        "level": "DEBUG",
        "progress": 0,
        "label": "文字起こしを開始しています...",
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

    output_file_path = Path(output_folder) / f"{input_file_path.stem}_transcription.txt"
    yield {
        "message": f"出力ファイル: {output_file_path}",
        "level": "INFO",
        "progress": 1.0,
        "label": "文字起こしを完了しました。",
    }

    with open(output_file_path, "w", encoding="utf-8") as f:
        for item in result:
            f.write(f"[{item['start']:.2f}s -> {item['end']:.2f}s] {item['text']}\n")

    yield {
        "message": "文字起こしが完了しました",
        "level": "INFO",
        "progress": 1.0,
        "label": "文字起こしを完了しました。",
    }


def transcription(
    settings,
    input_file,
    output_folder,
    logger,
    progress_bar,
    disabled_start_button,
):
    """
    文字起こしを実行する関数。
    """
    try:
        disabled_start_button(True)

        model = settings["model"]
        compute_type = settings["compute_type"]
        device = settings["device"]
        logger.info("文字起こしを開始します。")
        logger.debug(f"設定: {settings}")
        logger.debug(f"入力ファイル: {input_file}")
        logger.debug(f"出力フォルダ: {output_folder}")

        for update in _run_whisper(
            model,
            compute_type,
            device,
            input_file,
            output_folder,
        ):
            logger.add_log(update["message"], update["level"])
            progress_bar.update_value(update["progress"], update["label"])

    except Exception as e:
        logger.error(f"文字起こし中にエラーが発生しました: {e}")
        progress_bar.update_value(0, "エラーが発生しました")
    finally:
        disabled_start_button(False)
