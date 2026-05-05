# MyKokoro

<audio controls><source src="assets/intro.wav" type="audio/wav"></audio>

A fully offline, open-source Chinese text-to-speech application powered by [Kokoro-82M-v1.1-zh](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh).
It offers a clean **Gradio Web UI** (with download button) and a **FastAPI HTTPS API**, supporting **built-in Chinese voices**, custom `.pt` voice files, and adjustable speed.

> Apache 2.0 licensed
>
> No internet required after initial model download
>
> 🇨🇳 Optimised for Chinese + English mixed input

---

## Features

- **Web UI** — Input text, select a voice, adjust speed, generate & download WAV.
- **REST API** — `POST /tts` returns audio directly (easy to integrate with other apps).
- **Multi-voice** — Built-in Chinese voices (`zf_001`–`zf_004`, `zm_010`–`zm_014`) + custom `.pt` files from `voices/`.
- **Smart processing** — Automatic sentence splitting, natural pauses between sentences, and dynamic speed control to avoid rushed long sentences.
- **100% offline** — Works with pre-downloaded model and voice files (no recurring network calls).

---

## Project Structure

```

kokoro/
├── app.py # Main application (UI + API)
├── test_api.py # Example API client
├── kokoro_model/
│ └── voices/ # Built-in voice files (.pt)
├── voices/ # Your custom voice files (.pt)
├── requirements.txt # Python dependencies
└── README.md

```

or see [kokoro.html](assets/kokoro.html)

---

## Installation

clone the repository first.

enter the root of the project.

then build your environment:

```markdown
# python essential

python -m venv .venv
call .venv/scripts/activate
pip install kokoro>=0.8.2 misaki[zh]>=0.8.2 soundfile

# model download(need python env)

hf download hexgrad/Kokoro-82M-v1.1-zh --local-dir .\kokoro_model --force-download

# run

python .\kokoro_model\samples\make_zh.py

# caption

data in .cache is just links and real files is in the root.
```

## Usage

### Start the application

```bash
# Both Web UI and API (on ports 7860 and 8000)
python app.py --mode both --host 0.0.0.0 --port 7860 --api-port 8000

# Only Web UI
python app.py --mode ui --host 127.0.0.1 --port 7860

# Only API server
python app.py --mode api --host 0.0.0.0 --api-port 8000
```

### Web UI

Open your browser at `http://127.0.0.1:7860` and you will see:

- A text box for Chinese or mixed-language text.
- A voice selector (built-in + custom voices from the `voices/` folder).
- A speed slider (0.5–2.0).
- **Generate** button → listen to the result and **download** the WAV file.

### API

Send a POST request to `/tts` with the following parameters:

| Parameter | Type   | Required | Default  | Description                                              |
| --------- | ------ | -------- | -------- | -------------------------------------------------------- |
| `text`    | string | Yes      | –        | Text to synthesise (Chinese or mixed).                   |
| `voice`   | string | No       | `zf_001` | Voice name (e.g. `zf_004`) or full path to a `.pt` file. |
| `speed`   | float  | No       | `1.0`    | Speaking speed (0.5 – 2.0).                              |

**Example with Python (`requests`):**

```python
import requests

resp = requests.post(
    "http://127.0.0.1:8000/tts",
    params={"text": "你好世界", "voice": "zf_004", "speed": 1.2}
)
with open("hello.wav", "wb") as f:
    f.write(resp.content)
print("Success!" if resp.status_code == 200 else f"Error: {resp.text}")
```

You can also run `python test_api.py` to try it immediately.

---

## Adding Custom Voices

Place any `.pt` voice file (generated via fine-tuning or obtained from the community) inside the `voices/` folder.
The Web UI will automatically list them as **“自定义 - <filename>”**.

To use a custom voice via the API, pass its absolute path as the `voice` parameter.

---

## Tips

- **Speed control** — Values >1.0 speed up the reading, <1.0 slow it down. The app also dynamically reduces speed for very long sentences to keep the output natural.
- **Long texts** — The input is automatically split into sentences (by `。！？.!?`), and a brief silence is inserted between them.
- **English words** — The pipeline uses an internal `en_callable` to convert English words into phonemes, so mixed input sounds reasonable.

---

## License

This project is released under the **Apache License 2.0**.
The underlying Kokoro model is also Apache 2.0, and the Chinese voices provided are freely usable.
See the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh) by hexgrad
- The open-source TTS community

---

_Happy synthesising! If you use this project in your own work, a star or a mention would be much appreciated._
