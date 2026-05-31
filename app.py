"""
优化版中文 Kokoro TTS 应用：Web UI + 下载按钮 + HTTPS API
放置路径：D:\repos\Pelr\kokoro\app.py
自动识别 kokoro_model\voices\ 内置音色 与 voices\ 自定义音色。
"""

import os
import re
from pathlib import Path
import tempfile
import numpy as np
import soundfile as sf
import torch
from kokoro import KModel, KPipeline
import gradio as gr
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import uvicorn
import io
import threading
import argparse

# ========== 强制离线模式 ==========
os.environ["HF_HUB_OFFLINE"] = "1"

# ========== 配置 ==========
REPO_ID = 'hexgrad/Kokoro-82M-v1.1-zh'
SAMPLE_RATE = 24000
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

BASE_DIR = Path(__file__).resolve().parent
BUILTIN_VOICES_DIR = BASE_DIR / "kokoro_model" / "voices"
CUSTOM_VOICES_DIR = BASE_DIR / "voices"

N_ZEROS = 5000


def load_available_voices():
    voices = []
    if BUILTIN_VOICES_DIR.exists():
        for f in BUILTIN_VOICES_DIR.iterdir():
            if f.is_file() and f.suffix == ".pt":
                voices.append((f"内置 - {f.stem}", str(f)))
    if CUSTOM_VOICES_DIR.exists():
        for f in CUSTOM_VOICES_DIR.iterdir():
            if f.is_file() and f.suffix == ".pt":
                voices.append((f"自定义 - {f.stem}", str(f)))
    return voices


model = KModel(repo_id=REPO_ID).to(DEVICE).eval()
en_pipeline = KPipeline(lang_code='a', repo_id=REPO_ID, model=False)


def en_callable(text):
    if text == 'Kokoro':
        return 'kˈOkəɹO'
    elif text == 'Sol':
        return 'sˈOl'
    return next(en_pipeline(text)).phonemes


zh_pipeline = KPipeline(
    lang_code='z', repo_id=REPO_ID, model=model, en_callable=en_callable
)


def speed_callable(len_ps):
    speed = 0.9
    if len_ps <= 83:
        speed = 1.0
    elif len_ps < 183:
        speed = 1.0 - (len_ps - 83) / 500
    return speed * 1.1


def split_text(text):
    sentences = re.split(r'(?<=[。！？.!?])', text)
    return [s.strip() for s in sentences if s.strip()]


def synthesize_long(text: str, voice_id: str, speed_user: float = 1.0) -> np.ndarray:
    sentences = split_text(text)
    if not sentences:
        return np.zeros(0, dtype=np.float32)

    # 结合用户语速的最终速度函数
    def final_speed(len_ps):
        return speed_user * speed_callable(len_ps)

    audio_parts = []
    for sentence in sentences:
        gen = zh_pipeline(sentence, voice=voice_id, speed=final_speed)
        result = next(gen)
        wav = result.audio
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        audio_parts.append(wav)

    final = audio_parts[0]
    for part in audio_parts[1:]:
        final = np.concatenate([final, np.zeros(N_ZEROS, dtype=np.float32), part])
    return final


# ========== UI 修改 ==========
voice_choices = load_available_voices()


def tts_ui(text, voice_selection, speed):
    # voice_selection 直接就是本地路径
    audio = synthesize_long(text, voice_selection, speed)
    tmp_dir = Path(tempfile.gettempdir()) / "kokoro_tts"
    tmp_dir.mkdir(exist_ok=True)
    output_path = tmp_dir / "output.wav"
    sf.write(str(output_path), audio, SAMPLE_RATE)
    return str(output_path), str(output_path)


with gr.Blocks(title="Kokoro 中文 TTS") as demo:
    gr.Markdown("# 🎙️ Kokoro 中文语音合成（离线本地版）")
    gr.Markdown("音色文件全部从本地加载，无需联网。")

    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(
                label="输入文本", lines=6, placeholder="请输入中文或中英混合文本..."
            )
            voice_dropdown = gr.Dropdown(
                label="音色选择",
                choices=voice_choices,  # 直接使用元组列表
                value=voice_choices[0][1] if voice_choices else None,
            )
            speed_slider = gr.Slider(
                label="语速", minimum=0.5, maximum=2.0, value=1.0, step=0.1
            )
            submit_btn = gr.Button("生成语音", variant="primary")
        with gr.Column(scale=2):
            audio_output = gr.Audio(label="试听", type="filepath")
            file_download = gr.File(label="下载音频文件")

    submit_btn.click(
        fn=tts_ui,
        inputs=[text_input, voice_dropdown, speed_slider],
        outputs=[audio_output, file_download],
    )

# ========== FastAPI ==========
app = FastAPI(title="Kokoro TTS API")


@app.post("/tts")
async def tts_api(
    text: str = Query(..., description="要合成的文本"),
    voice: str = Query("zf_001", description="音色标识（内置名称或 .pt 文件路径）"),
    speed: float = Query(1.0, ge=0.5, le=2.0, description="语速"),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")
    # 如果传入的是名称，补全为本地路径
    if not os.path.isfile(voice):
        voice_path = BUILTIN_VOICES_DIR / f"{voice}.pt"
        if voice_path.exists():
            voice = str(voice_path)
        else:
            raise HTTPException(status_code=404, detail=f"音色文件不存在: {voice}")
    try:
        audio = synthesize_long(text, voice, speed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    buffer = io.BytesIO()
    sf.write(buffer, audio, SAMPLE_RATE, format='WAV')
    buffer.seek(0)
    return Response(content=buffer.read(), media_type="audio/wav")


# ========== OpenAI-Compatible API ==========


@app.post("/v1/audio/speech")
async def tts_openai(body: dict):
    input_text = body.get("input", "")
    voice = body.get("voice", "zf_001")
    speed = body.get("speed", 1.0)
    response_format = body.get("response_format", "wav")

    if not input_text.strip():
        raise HTTPException(status_code=400, detail="input must not be empty")

    if not os.path.isfile(voice):
        voice_path = BUILTIN_VOICES_DIR / f"{voice}.pt"
        if voice_path.exists():
            voice = str(voice_path)
        else:
            raise HTTPException(status_code=404, detail=f"Voice not found: {voice}")

    try:
        audio = synthesize_long(input_text, voice, speed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if response_format == "pcm":
        buffer = io.BytesIO()
        sf.write(buffer, audio, SAMPLE_RATE, format='RAW', subtype='PCM_16')
        buffer.seek(0)
        return Response(content=buffer.read(), media_type="audio/L16;rate=24000;channels=1")
    elif response_format in ("wav", "flac"):
        buffer = io.BytesIO()
        sf.write(buffer, audio, SAMPLE_RATE, format=response_format.upper())
        buffer.seek(0)
        return Response(content=buffer.read(), media_type=f"audio/{response_format}")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported response_format: {response_format}. Supported: wav, flac, pcm")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kokoro Chinese TTS WebUI & API")
    parser.add_argument("--mode", choices=["ui", "api", "both"], default="both")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--api-port", type=int, default=8000)
    args = parser.parse_args()

    if args.mode in ("ui", "both"):
        if args.mode == "both":
            api_thread = threading.Thread(
                target=lambda: uvicorn.run(
                    app, host=args.host, port=args.api_port, log_level="info"
                ),
                daemon=True,
            )
            api_thread.start()
            print(f"API 服务已启动于 http://{args.host}:{args.api_port}")
        print(f"Web UI 启动于 http://{args.host}:{args.port}")
        demo.launch(server_name=args.host, server_port=args.port, share=False)
    elif args.mode == "api":
        uvicorn.run(app, host=args.host, port=args.api_port, log_level="info")

"""
python app.py --mode ui --host 0.0.0.0 --port 7860
python app.py --mode api --host 0.0.0.0 --api-port 8000
python app.py --mode both --host 0.0.0.0 --port 7860 --api-port 8000
"""
