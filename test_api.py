import requests

resp = requests.post(
    "http://127.0.0.1:8000/tts",
    params={"text": "你好世界", "voice": "zf_004", "speed": 1.2},
)
with open("hello.wav", "wb") as f:
    f.write(resp.content)
print("success!" if resp.status_code == 200 else f"错误：{resp.text}")
