# Kokoro TTS — Agent Guide

## Overview

A Gradio Web UI + FastAPI HTTPS API for Chinese/English TTS using [Kokoro-82M-v1.1-zh](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh). Fully offline after initial model download.

## Commands

```bash
pip install -r requirements.txt                       # install deps
python app.py --mode both --host 0.0.0.0 --port 7860 --api-port 8000  # full app
python app.py --mode ui   --host 127.0.0.1 --port 7860                # UI only
python app.py --mode api  --host 0.0.0.0 --api-port 8000              # API only
python test_api.py  # quick API smoke test (needs server on :8000)
```

## Key files

| Path | Purpose |
|------|---------|
| `app.py` | Single-file app: Gradio UI, FastAPI server, TTS pipeline |
| `test_api.py` | Minimal `requests`-based API client example |
| `kokoro_model/` | Model weights & 103 built-in `.pt` voice files |
| `voices/` | User-placed custom `.pt` voice files (auto-detected) |

## Architecture notes

- **Entrypoint**: `app.py` only. No framework, no build step.
- **Offline by default**: `os.environ["HF_HUB_OFFLINE"] = "1"` at module top. Model must be pre-downloaded.
- **Model download**: `hf download hexgrad/Kokoro-82M-v1.1-zh --local-dir .\kokoro_model --force-download`
- **Single pipeline**: One `KModel` + `KPipeline(lang_code='z')` with an `en_callable` for mixed Chinese+English.
- **UI & API share the same pipeline**; API runs in a daemon thread alongside UI in `both` mode.
- **API endpoints**: `POST /tts` (legacy, query params, WAV only) and `POST /v1/audio/speech` (OpenAI-compatible, JSON body, supports `wav`/`flac`/`pcm`).
- **Voice resolution**: Both endpoints accept short names (e.g. `zf_001`) or full `.pt` paths; UI dropdown lists both built-in and custom voices.
- **Audio output**: 24 kHz, supports WAV, FLAC, PCM via the OpenAI endpoint; legacy endpoint returns WAV only.

## Repo structure quirks

- `kokoro_model/voices/` is **gitignored** (model download produces it). The repo commits voice files under `kokoro_model/voices/` but `.gitignore` would exclude new ones — rely on the actual filesystem state.
- `cmd` directory at root is gitignored (simple command notes, not a real dir).
- `kokoro_model/.cache/` is gitignored (HF symlink cache).
- The Gradio download button works via a temp file (`tmp_dir/kokoro_tts/output.wav`).
- No tests beyond `test_api.py` (manual smoke test). No lint/typecheck/CI config exists.

## Voice files

- **Built-in** (103 voices): `kokoro_model/voices/*.pt` — female (`zf_*`), male (`zm_*`), English (`af_*`, `bf_*`).
- **Custom**: Put `.pt` files in `voices/` at repo root. UI shows them as `"自定义 - <name>"`.
- API default voice is `zf_001`.

## Style conventions

- Code is in Chinese+English mixed comments. The `app.py` docstring and some comments are in Chinese.
- No formatter, linter, or type checker configured — don't add one without asking.
- Single-file app design; keep it that way unless there's a strong reason to split.
