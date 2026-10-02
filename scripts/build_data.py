"""크롤링 CSV -> 덱 전체가 공유하는 data/models.json (단일 데이터 원본)"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "data" / "models.json"
STAMP = "20261002_1102"
PRODUCTS = ROOT / "output" / f"schoolmusic_bass_year_products_{STAMP}.csv"
REVIEWS = ROOT / "output" / f"schoolmusic_bass_year_reviews_{STAMP}.csv"

# (키, 표시명, 브랜드, 상품명 매칭 문자열)
MODELS = [
    ("abp", "Cort Action Bass Plus", "Cort", "Action Bass Plus"),
    ("apj", "Cort Action PJ", "Cort", "Action PJ"),
    ("tjb", "Twoman TJB-120", "Twoman", "TJB-120"),
    ("gb24", "Cort GB24JJ", "Cort", "GB24JJ"),
    ("gsr", "Ibanez GSR180", "Ibanez", "GSR180"),
    ("hex", "Hex B100", "Hex", "Hex B100"),
    ("swing", "Swing Jazz King", "Swing", "Jazz King"),
    ("gw", "GopherWood J-Classic IV", "GopherWood", "GopherWood"),
    ("c4", "Cort C4 Plus OVMH", "Cort", "C4 Plus"),
    ("bb", "Yamaha BB234", "Yamaha", "BB234"),
]
PICKS = {"abp": "가성비 1순위", "hex": "안정성", "gsr": "소리·가벼움", "bb": "예산 최대"}

# 리뷰를 직접 읽고 분류한 악기 결함 리뷰 (배송·사은품 누락은 제외)
DEFECTS = {
    "apj": ["2025-05-25", "2019-01-19"],
    "gb24": ["2025-12-20"],
    "swing": ["2025-09-09", "2025-04-21", "2023-03-30", "2026-02-27"],
    "bb": ["2024-06-20"],
}
TOPICS = {
    "디자인·색상": r"예쁘|이쁘|예뻐|이뻐|색|디자인|존예|멋",
    "입문·초보": r"입문|초보|처음|첫|베린이|연습용",
    "배송·포장": r"배송|포장|택배|도착",
    "소리·톤": r"소리|톤|음색|울림|사운드",
    "가성비·가격": r"가성비|가격|저렴|싸고|세일|가선비",
    "구성품·긱백": r"구성품|사은품|가방|긱백|케이스|케이블|스트랩",
}
PRIOR_MEAN, PRIOR_WEIGHT = 4.8, 5  # 리뷰 수가 적은 모델의 평점을 전체 평균 쪽으로 당기는 보정


def match(name):
    for key, *_rest, needle in MODELS:
        if needle in name:
            return key
    return None


def main():
    products = list(csv.DictReader(open(PRODUCTS, encoding="utf-8-sig")))
    reviews = list(csv.DictReader(open(REVIEWS, encoding="utf-8-sig")))

    ranks = [{"rank": 1, "model": None, "brand": "패키지", "name": "[스쿨뮤직 패키지] 베이스 구성품"}]
    for p in products:
        key = match(p["상품명"])
        brand = next(m[2] for m in MODELS if m[0] == key)
        ranks.append({"rank": int(p["순위"]), "model": key, "brand": brand, "name": p["상품명"]})

    models = []
    for key, label, brand, _ in MODELS:
        ps = [p for p in products if match(p["상품명"]) == key]
        rs = [r for r in reviews if match(r["상품명"]) == key]
        scores = [int(r["평점"]) for r in rs]
        dist = Counter(scores)
        n = len(scores)
        avg = sum(scores) / n
        adj = (n * avg + PRIOR_WEIGHT * PRIOR_MEAN) / (n + PRIOR_WEIGHT)
        price = min(int(p["판매가"]) for p in ps)
        models.append({
            "key": key, "name": label, "brand": brand,
            "price": price, "list": int(ps[0]["정가"]),
            "discount": round(100 * (1 - price / int(ps[0]["정가"]))),
            "ranks": sorted(int(p["순위"]) for p in ps),
            "n": n, "avg": round(avg, 2), "adj": round(adj, 3),
            "dist": [dist.get(s, 0) for s in (5, 4, 3, 2, 1)],
            "five_pct": round(100 * dist.get(5, 0) / n),
            "defects": len(DEFECTS.get(key, [])),
            "recent": sum(r["작성일"] >= "2025-01-01" for r in rs),
            "value": round(adj / (price / 100000), 3),
            "pick": PICKS.get(key),
        })

    years = Counter(r["작성일"][:4] for r in reviews)
    data = {
        "collected": "2026-10-02",
        "totals": {
            "ranked": 20, "products": len(products), "models": len(models),
            "reviews": len(reviews), "photo_reviews": sum(bool(r["이미지"]) for r in reviews),
            "avg": round(sum(int(r["평점"]) for r in reviews) / len(reviews), 2),
            "since_2023_pct": round(100 * sum(r["작성일"] >= "2023" for r in reviews) / len(reviews)),
        },
        "models": models,
        "ranks": sorted(ranks, key=lambda r: r["rank"]),
        "years": [{"year": y, "n": years[y]} for y in sorted(years)],
        "topics": [{"topic": t, "n": sum(bool(re.search(p, r["내용"])) for r in reviews)}
                   for t, p in TOPICS.items()] + [{"topic": "결함·불량", "n": sum(len(v) for v in DEFECTS.values()), "neg": True}],
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    # file:// 로 열어도 동작하도록 같은 데이터를 스크립트로도 내보냄
    OUT.with_suffix(".js").write_text("window.DECK_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"wrote {OUT} (+ .js)")
    for m in sorted(models, key=lambda m: -m["value"]):
        print(f"{m['name']:<26} {m['price']:>8,} n={m['n']:>2} avg={m['avg']} adj={m['adj']} value={m['value']} dist={m['dist']} defects={m['defects']}")
    print(data["totals"], data["years"], data["topics"], sep="\n")


if __name__ == "__main__":
    main()
