"""스쿨뮤직(schoolmusic.co.kr) 인기 베이스기타 + 구매후기 크롤러

판매순위 페이지(베이스기타 카테고리)에서 인기 상품을 가져온 뒤,
각 상품 페이지의 '일반 구매 후기'를 페이지별로 수집한다.

사용법:
    python crawl_schoolmusic_bass.py                      # 월간 판매순위 10위까지, 상품당 후기 최대 5페이지(50개)
    python crawl_schoolmusic_bass.py --period week --top 20 --review-pages 0   # 0 = 후기 전체
    python crawl_schoolmusic_bass.py --include-packages   # '[스쿨뮤직 패키지]' 구성품 상품도 포함
"""
import argparse
import csv
import html
import json
import re
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent
BASE_URL = "https://www.schoolmusic.co.kr/Shop/index.php3"
BASS_CATEGORY = 4  # 베이스기타
REVIEWS_PER_PAGE = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def fetch(url, delay=0.5):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
    time.sleep(delay)
    return body.decode("cp949", errors="replace")  # 사이트가 EUC-KR


def clean(fragment):
    """HTML 조각 -> 텍스트 (줄바꿈 보존)"""
    text = re.sub(r"<br\s*/?>|</p>", "\n", fragment, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    lines = [ln.strip() for ln in text.splitlines()]
    return re.sub(r"\n{2,}", "\n", "\n".join(ln for ln in lines if ln)).strip()


def to_int(s):
    digits = re.sub(r"[^\d]", "", s or "")
    return int(digits) if digits else None


# ---------------------------------------------------------------- 판매순위
def parse_ranking(page):
    marker = "onClick=\"javascript:location.href='/Shop/index.php3?var=Good&Good_no="
    items = []
    for rank, block in enumerate(page.split(marker)[1:], start=1):
        good_no = int(re.match(r"\d+", block).group())
        name_m = re.search(r'<tr height="55">.*?<font color="#393939">(.*?)</font>', block, re.S)
        prices = re.findall(r"([\d,]+)원", block)
        discount = re.search(r'font-size:26px[^>]*>(\d+)</font>', block)
        likes = re.search(r"chuchen_area_[^>]*>\s*([\d,]+)", block)
        name = clean(name_m.group(1)) if name_m else ""
        items.append({
            "순위": rank,
            "상품번호": good_no,
            "상품명": name.replace("\n", " "),
            "정가": to_int(prices[0]) if len(prices) > 1 else None,
            "판매가": to_int(prices[-1]) if prices else None,
            "할인율": f"{discount.group(1)}%" if discount else "",
            "좋아요": to_int(likes.group(1)) if likes else None,
            "URL": f"{BASE_URL}?var=Good&Good_no={good_no}",
        })
    return items


# ---------------------------------------------------------------- 구매후기
def count_stars(fragment):
    return len(re.findall(r"icon_star2?_on", fragment))


def parse_reviews(page):
    total = re.search(r"일반 구매 후기</font><strong>\(\s*(\d+)", page)
    total = int(total.group(1)) if total else 0

    reviews = []
    area = page.split('<a name="after_area"></a>', 1)[-1]
    area = area.split('id="qa_area"', 1)[0].split('name="qa_area"', 1)[0]
    # 각 후기 = 요약 행(<tr height="85">) + 본문(table id="after_N") → 요약 행 기준으로 분할
    for chunk in area.split('<tr height="85">')[1:]:
        head, _, body = chunk.partition("</tr>")
        if "open_content('after'" not in head:
            continue
        cells = re.findall(r"<td[^>]*>(.*?)(?=<td|$)", head, re.S)
        title = re.search(r"open_content\('after',\d+\)\">(.*?)</span>", head, re.S)
        date = re.search(r"(\d{4}-\d{2}-\d{2})", head)

        content_m = re.search(r"<div style='width:770px[^>]*>(.*?)</div>\s*</td>", body, re.S)
        content = clean(content_m.group(1)) if content_m else ""
        images = re.findall(r'<img[^>]+src="([^"]+)"[^>]*(?:class="photo"|style="width: 100%")', body)

        sub = {}
        for label, stars in re.findall(r"(성능|가격|디자인|배송)\s*((?:<img[^>]*>\s*)+)", body):
            sub[label] = count_stars(stars)

        reviews.append({
            "평점": count_stars(cells[0]) if cells else None,
            "제목": clean(title.group(1)) if title else "",
            "구분": clean(cells[3]) if len(cells) > 3 else "",
            "작성자": clean(cells[4]) if len(cells) > 4 else "",
            "작성일": date.group(1) if date else "",
            "내용": content,
            "성능": sub.get("성능"), "가격": sub.get("가격"),
            "디자인": sub.get("디자인"), "배송": sub.get("배송"),
            "이미지": " ".join(images),
        })
    return total, reviews


def crawl_reviews(good_no, max_pages):
    first = fetch(f"{BASE_URL}?var=Good&Good_no={good_no}")
    total, reviews = parse_reviews(first)
    last_page = -(-total // REVIEWS_PER_PAGE)
    if max_pages:
        last_page = min(last_page, max_pages)
    for p in range(2, last_page + 1):
        _, more = parse_reviews(fetch(
            f"{BASE_URL}?page={p}&var=Good&Good_no={good_no}&page_mode=after_note"))
        if not more:
            break
        reviews.extend(more)
    return total, reviews


# ---------------------------------------------------------------- main
def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", choices=["week", "month", "year"], default="month",
                        help="판매순위 기간 (기본: month)")
    parser.add_argument("--top", type=int, default=10, help="판매순위 몇 위까지 조사할지")
    parser.add_argument("--review-pages", type=int, default=5,
                        help="상품당 후기 최대 페이지(10개/페이지), 0 = 전체")
    parser.add_argument("--include-packages", action="store_true",
                        help="'[스쿨뮤직 패키지]' 같은 구성품 상품도 포함")
    args = parser.parse_args()

    # 기본 페이지는 10위까지만 보여줌 → 검색폼(mode=search) + 기간값 + top 파라미터로 확장
    now = datetime.now()
    period_param = {
        "year": f"year_no={now:%Y}y",
        "month": f"month_no={now:%Y%m}m",
        "week": f"week_no={now - timedelta(days=now.weekday()):%Y%m%d}w",
    }[args.period]
    url = (f"{BASE_URL}?var=sale_top&s_mode={args.period}&large_no={BASS_CATEGORY}"
           f"&{period_param}&top={args.top}&mode=search")
    print(f"판매순위 크롤링: {url}")
    ranking = parse_ranking(fetch(url))
    if not ranking:
        raise RuntimeError("판매순위 목록을 찾지 못했습니다.")
    if not args.include_packages:
        ranking = [r for r in ranking if "패키지]" not in r["상품명"]]
    products = ranking[:args.top]

    all_reviews = []
    for prod in products:
        total, reviews = crawl_reviews(prod["상품번호"], args.review_pages)
        prod["후기수"] = total
        rated = [r["평점"] for r in reviews if r["평점"]]
        prod["평균평점(수집분)"] = round(sum(rated) / len(rated), 2) if rated else None
        prod["수집후기수"] = len(reviews)
        for r in reviews:
            all_reviews.append({"순위": prod["순위"], "상품번호": prod["상품번호"],
                                "상품명": prod["상품명"], **r})
        print(f"{prod['순위']:>3}. {prod['상품명'][:50]:<50}  {prod['판매가'] or 0:>9,}원  "
              f"후기 {len(reviews)}/{total}  평균 {prod['평균평점(수집분)']}")

    out_dir = BASE_DIR.parent / "data" / "raw"  # 덱 데이터 원본 폴더
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    prod_csv = out_dir / f"schoolmusic_bass_{args.period}_products_{stamp}.csv"
    rev_csv = out_dir / f"schoolmusic_bass_{args.period}_reviews_{stamp}.csv"
    json_path = out_dir / f"schoolmusic_bass_{args.period}_{stamp}.json"

    write_csv(prod_csv, products, list(products[0].keys()))
    if all_reviews:
        write_csv(rev_csv, all_reviews, list(all_reviews[0].keys()))
    json_path.write_text(json.dumps(
        [{**p, "후기": [r for r in all_reviews if r["상품번호"] == p["상품번호"]]} for p in products],
        ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n상품 {len(products)}개 / 후기 {len(all_reviews)}개 저장 완료\n"
          f"  {prod_csv}\n  {rev_csv}\n  {json_path}")


if __name__ == "__main__":
    main()
