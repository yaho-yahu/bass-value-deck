"""nanobanana(Gemini 이미지 모델)로 덱 이미지 에셋 생성 -> assets/img/*.jpg
키: 저장소 루트 .env 의 GEMINI_API_KEY (결제 연결된 Google AI Studio 프로젝트 필요)
사용법: python scripts/gen_images.py [이름 ...]   (이름 생략 시 전부)
"""
import base64
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parents[1]
ENV = BASE / ".env"  # 저장소 루트 .env (git 제외). .env.example 참고
OUT = BASE / "assets" / "img"
API = "https://generativelanguage.googleapis.com/v1beta"
import os
PREFERRED = [m for m in [os.environ.get("IMAGE_MODEL")] if m] + ["gemini-3-pro-image-preview", "gemini-2.5-flash-image", "gemini-2.5-flash-image-preview"]

STYLE = ("Photorealistic editorial photograph, cinematic low-key lighting, warm amber practical light against deep "
         "navy shadows, shallow depth of field, 35mm film look. Absolutely no text, no letters, no logos, no brand "
         "names, no watermarks anywhere in the image.")
IMAGES = {
    "hero": ("16:9", "A four-string electric bass guitar leaning against a small practice amplifier in a dim home "
             "rehearsal room, the bass placed on the right third of the frame, empty dark space on the left. " + STYLE),
    "unboxing": ("4:3", "A teenage student at home unzipping a brand-new padded gig bag to reveal an electric bass "
                 "guitar, hands and instrument in focus, face partly out of frame, cozy bedroom at evening. " + STYLE),
    "strings": ("16:9", "Extreme close-up of electric bass guitar strings running over two single-coil pickups and a "
                "chrome bridge, strong diagonal composition. " + STYLE),
    "rehearsal": ("16:9", "A bassist seen from behind in silhouette on a small rehearsal stage, warm spotlight haze, "
                  "amplifiers and a drum kit softly blurred in the background, darker lower area of the frame. " + STYLE),
}


def api_key():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("=")
        if k.strip() == "GEMINI_API_KEY" and v.strip():
            return v.strip().strip('"').strip("'")
    sys.exit(".env 에 GEMINI_API_KEY 가 없습니다.")


def call(url, body=None, key=""):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def pick_model(key):
    names = [m["name"].split("/")[-1] for m in call(f"{API}/models?pageSize=200", key=key).get("models", [])]
    for p in PREFERRED:
        if p in names:
            return p
    image_models = [n for n in names if "image" in n and "gemini" in n]
    if not image_models:
        sys.exit(f"이미지 생성 모델을 찾지 못했습니다: {names}")
    return image_models[0]


def generate(model, key, name, ratio, prompt):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": ratio}}}
    data = call(f"{API}/models/{model}:generateContent", body, key)
    for part in data["candidates"][0]["content"]["parts"]:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline:
            img = Image.open(io.BytesIO(base64.b64decode(inline["data"]))).convert("RGB")
            img.thumbnail((1920, 1920))
            OUT.mkdir(parents=True, exist_ok=True)
            path = OUT / f"{name}.jpg"
            img.save(path, quality=86, optimize=True, progressive=True)
            return path, img.size
    raise RuntimeError(f"{name}: 이미지가 응답에 없습니다: {json.dumps(data)[:400]}")


def main():
    key = api_key()
    model = pick_model(key)
    print("model:", model)
    targets = [a for a in sys.argv[1:] if a in IMAGES] or list(IMAGES)
    for name in targets:
        ratio, prompt = IMAGES[name]
        try:
            path, size = generate(model, key, name, ratio, prompt)
            print(f"saved {path.name} {size}")
        except urllib.error.HTTPError as e:
            print(f"{name}: HTTP {e.code} {e.read()[:300]!r}")


if __name__ == "__main__":
    main()
