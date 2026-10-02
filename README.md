# 50만원 베이스 가성비 리포트 (HTML 슬라이드)

스쿨뮤직 2026 연간 판매순위 베이스기타 1–20위, 구매후기 170건 분석 덱입니다.

- 보기: `index.html` (← → / Space 로 넘기기, F 전체화면)
- 차트·전환: anime.js · SVG / 정적 차트: matplotlib / 설명 애니메이션: manim
- 데이터: `data/models.json` (크롤링 CSV에서 `scripts/build_data.py`로 생성)

## 다시 만들기
```
python scripts/build_data.py      # CSV -> data/models.json, models.js
python scripts/make_charts.py     # matplotlib -> assets/charts/*.svg
python -m manim -r 1600,900 --fps 30 scripts/scenes.py Funnel ValueIndex
python scripts/gen_images.py      # nanobanana(Gemini) -> assets/img/*.jpg (GEMINI_API_KEY 필요)
python scripts/verify_data.py     # 덱 수치를 CSV와 대조
node scripts/shots.mjs            # 슬라이드별 검증 스크린샷
```
