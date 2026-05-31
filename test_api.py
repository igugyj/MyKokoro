import requests

# === Legacy API (query params) ===
resp = requests.post(
    "http://127.0.0.1:8000/tts",
    params={"text": "你好世界", "voice": "zf_004", "speed": 1.2},
)
with open("hello_legacy.wav", "wb") as f:
    f.write(resp.content)
print("legacy API:", "success!" if resp.status_code == 200 else f"错误：{resp.text}")

# === OpenAI-compatible API (JSON body) ===
resp = requests.post(
    "http://127.0.0.1:8000/v1/audio/speech",
    json={
        "model": "kokoro-82m-v1.1-zh",
        "input": "你好世界，欢迎使用语音合成。",
        "voice": "zf_004",
        "speed": 1.2,
        "response_format": "wav",
    },
)
with open("hello_openai.wav", "wb") as f:
    f.write(resp.content)
print("OpenAI API:", "success!" if resp.status_code == 200 else f"错误：{resp.text}")
