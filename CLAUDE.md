# bass-value-deck — 작업 인수인계

스쿨뮤직(schoolmusic.co.kr) 2026 연간 판매순위 베이스기타 1–20위의 구매후기 170건을 분석해
"50만원 이하 가성비 베이스"를 추천하는 HTML 슬라이드 덱. GitHub Pages로 배포됨.

- 배포: https://yaho-yahu.github.io/bass-value-deck/
- 저장소: https://github.com/yaho-yahu/bass-value-deck
- 마지막 작업: 2026-10-02

## 현재 상태
- [x] 크롤링 (`crawler/crawl_schoolmusic_bass.py`) → `data/raw/*.csv` (상품 19개, 리뷰 170건, 사이트 표시 건수와 100% 일치)
- [x] 14장 덱 `index.html` (anime.js 차트·전환, matplotlib SVG 3개, manim mp4 2개)
- [x] 데이터 검증 `scripts/verify_data.py` 103개 항목 통과
- [x] 렌더 검증 (데스크톱 14장 + 모바일) 및 Pages 배포, 에셋 전부 HTTP 200
- [ ] **nanobanana 이미지 4장 미생성** — Gemini 이미지 모델이 무료 등급 할당량 0(`limit: 0`)이라 429.
      Google AI Studio 프로젝트에 결제 연결 후 아래 "이미지 추가" 절차 실행. 그 전까지 이미지 자리는 그라데이션으로 대체됨.
- 참고 보고서(단일 HTML): `report/bass_value_report.html`

## 다른 PC에서 이어서 하기
```bash
git clone https://github.com/yaho-yahu/bass-value-deck.git && cd bass-value-deck
gh auth login                                  # 배포(push)할 때 필요
pip install -r requirements.txt                # matplotlib, pillow
python -m pip install uv && python -m uv venv .venv-manim --python 3.12
python -m uv pip install --python .venv-manim/Scripts/python.exe manim   # manim은 Python 3.14 미지원 → 3.12 venv
cp .env.example .env                           # GEMINI_API_KEY 채우기 (git에 안 올라감)
```
Node 22+ (검증 스크린샷), Chrome (`C:\Program Files\Google\Chrome\Application\chrome.exe`, 다른 경로면 `scripts/shots.mjs`의 CHROME 수정) 필요.

## 이미지 추가 (남은 작업)
```bash
python scripts/gen_images.py                   # hero, unboxing, strings, rehearsal → assets/img/*.jpg
IMAGE_MODEL=gemini-2.5-flash-image python scripts/gen_images.py   # Pro 모델 대신 기본 Nano Banana
node scripts/shots.mjs                         # 1·9·12·14번 슬라이드 확인 (이미지 쓰는 곳)
git add assets/img && git commit && git push   # Pages 자동 재배포
```

## 전체 재생성 파이프라인
1. `python crawler/crawl_schoolmusic_bass.py --period year --top 20 --review-pages 0` → `data/raw/`
2. `python scripts/build_data.py` → `data/models.json`, `data/models.js` (모든 시각화의 단일 데이터 원본)
3. `python scripts/make_charts.py` → `assets/charts/*.svg`
4. `.venv-manim/Scripts/python -m manim -r 1600,900 --fps 30 --media_dir build/manim scripts/scenes.py Funnel ValueIndex`
   → mp4를 `assets/video/`에 복사, `-s`로 뽑은 마지막 프레임을 같은 이름 `.png` 포스터로 복사
5. `python scripts/verify_data.py` (덱 본문 수치가 바뀌면 이 스크립트의 기대 문구도 함께 수정)
6. `node scripts/shots.mjs [--mobile] [--url=배포URL] [슬라이드번호...]` → `build/screens/` 확인

## 작업 방식 (사용자 선호)
- 슬라이드 작업은 **항상 계획 먼저**(`PLAN.md` 갱신) → 구현 → **검증 루프**(데이터 대조 + 스크린샷 확인 + 수정 반복).
- HTML을 요청하면 로컬 파일로 만든다. claude.ai 아티팩트로 임의 게시하지 않는다.
- 배포는 GitHub CLI + Pages. 로그인이 필요하면 `gh auth login --web`을 띄워 사용자가 기기 코드를 입력하게 한다.
- API 키는 `.env`에만. 채팅에 붙여넣은 키는 회전(재발급) 권장.

## 분석상 결정 사항
- 1위 "[스쿨뮤직 패키지] 베이스 구성품"은 베이스 본체가 아니라 제외 → 19개 상품을 색상 옵션별로 묶어 10개 모델.
- 결함 리뷰는 직접 읽고 분류(`build_data.py`의 `DEFECTS`): 버징·흠집·세팅 불량만, 사은품 누락 같은 배송 문제는 제외.
- 가성비 지수 = 보정 평점 ÷ 판매가(10만원), 보정 평점 = (n·평균 + 5·4.8)/(n+5).
- 세부 평점(성능·가격·디자인·배송)은 170건 중 168건이 종합 평점과 같아 사용 안 함.
- 결론: 가성비 1순위 Cort Action Bass Plus(251,100원, 4.91점, 결함 0), 안정성 Hex B100, 소리·가벼움 Ibanez GSR180, 예산 최대 Yamaha BB234. 주의: Swing Jazz King(결함 4/53), Cort GB24JJ(목재 지적).
- 판매순위 페이지는 기본 10위까지만 표시 → `mode=search` + 기간값(`year_no=2026y`) + `top=20` 파라미터로 확장(크롤러에 반영됨).

## 검증 시 주의
- 헤드리스 Chrome은 기본으로 `prefers-reduced-motion: reduce`. `shots.mjs`는 이를 끄고 실시간 대기 후 캡처한다(`--reduced`로 감소 모드 확인).
- `--virtual-time-budget` 방식은 애니메이션이 중간에 멈춘 채 찍히므로 쓰지 않는다.
