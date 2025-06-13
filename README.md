# whisper-app
GUIでwhisperが使えるように

だいぶきたないコードなので(特にwhisperのあたり)、もうちょっと綺麗にする予定

## 使い方

(必要に応じて)uvをインストール

参考 : https://docs.astral.sh/uv/

依存関係をインストール
```bash
uv sync
```

仮想環境を有効化した後

```bash
python app/main.py
```

で実行

## GPU を使う場合
`uv` で `PyTorch` を使う場合

参考 : https://docs.astral.sh/uv/guides/integration/pytorch/

### 例 ; cuda 12.8 の場合
pyproject.toml
```toml
[project]
name = "whisper-app"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "faster-whisper>=1.1.1",
    "flet[all]>=0.28.3",
    "rich>=14.0.0",
    "torch==2.7.1",
    "torchaudio==2.7.1",
    "torchvision==0.22.1",
]

[tool.taskipy.tasks]
start = "python app/main.py"

[tool.uv.sources]
torch = [{ index = "pytorch-cu128" }]
torchvision = [{ index = "pytorch-cu128" }]

[[tool.uv.index]]
name = "pytorch-cu128"
url = "https://download.pytorch.org/whl/cu128"
explicit = true
```