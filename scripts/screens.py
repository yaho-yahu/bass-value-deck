"""검증용 스크린샷: 헤드리스 Chrome으로 슬라이드마다 캡처 -> build/screens/
사용법: python scripts/screens.py [슬라이드번호 ...] [--mobile]
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = BASE / "build" / "screens"
OUT.mkdir(parents=True, exist_ok=True)
URL = (BASE / "index.html").as_uri()


def shot(n, w, h, tag):
    out = OUT / f"{tag}{n:02d}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
                    f"--window-size={w},{h}", "--virtual-time-budget=7000",
                    "--autoplay-policy=no-user-gesture-required",
                    f"--user-data-dir={BASE / 'build' / ('prof' + tag + str(n))}",
                    f"--screenshot={out}", f"{URL}#{n}"],
                   capture_output=True, timeout=90)
    return out


def main():
    mobile = "--mobile" in sys.argv
    nums = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(1, 15))
    w, h, tag = (390, 844, "m") if mobile else (1600, 900, "s")
    with ThreadPoolExecutor(4) as ex:
        for p in ex.map(lambda n: shot(n, w, h, tag), nums):
            print(p.name, p.exists() and p.stat().st_size)


if __name__ == "__main__":
    main()
