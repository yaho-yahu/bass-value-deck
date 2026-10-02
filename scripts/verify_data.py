"""데이터 검증: 덱(index.html)에 적힌 수치를 크롤링 CSV에서 독립적으로 다시 계산해 대조한다.
불일치가 하나라도 있으면 exit 1.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw"
HTML = (BASE / "index.html").read_text(encoding="utf-8")
DATA = json.loads((BASE / "data" / "models.json").read_text(encoding="utf-8"))
P = list(csv.DictReader(open(sorted(RAW.glob("schoolmusic_bass_year_products_*.csv"))[-1], encoding="utf-8-sig")))
R = list(csv.DictReader(open(sorted(RAW.glob("schoolmusic_bass_year_reviews_*.csv"))[-1], encoding="utf-8-sig")))

fails = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (f"  ({detail})" if detail else ""))
    if not ok:
        fails.append(label)


def in_html(label, text):
    check(f"본문 문구 존재: {label}", text in HTML, text)


def rev(needle):
    return [r for r in R if needle in r["상품명"]]


# 1) models.json 이 CSV와 일치하는지
check("상품 수 19", len(P) == 19 == DATA["totals"]["products"])
check("리뷰 수 170", len(R) == 170 == DATA["totals"]["reviews"])
for p in P:
    total = int(p["후기수"])
    got = sum(1 for r in R if r["상품번호"] == p["상품번호"])
    check(f"상품 {p['상품번호']} 후기 {got}/{total}", got == total)
for m in DATA["models"]:
    needle = {"abp": "Action Bass Plus", "apj": "Action PJ", "tjb": "TJB-120", "gb24": "GB24JJ", "gsr": "GSR180",
              "hex": "Hex B100", "swing": "Jazz King", "gw": "GopherWood", "c4": "C4 Plus", "bb": "BB234"}[m["key"]]
    rs = rev(needle)
    sc = [int(r["평점"]) for r in rs]
    price = min(int(p["판매가"]) for p in P if needle in p["상품명"])
    check(f"{m['name']} 리뷰 수 {m['n']}", len(rs) == m["n"])
    check(f"{m['name']} 평균 {m['avg']}", round(sum(sc) / len(sc), 2) == m["avg"])
    check(f"{m['name']} 판매가 {m['price']}", price == m["price"])
    check(f"{m['name']} 분포 {m['dist']}", [Counter(sc).get(s, 0) for s in (5, 4, 3, 2, 1)] == m["dist"])
    adj = (len(sc) * (sum(sc) / len(sc)) + 5 * 4.8) / (len(sc) + 5)
    check(f"{m['name']} 가성비 지수 {m['value']}", abs(adj / (price / 1e5) - m["value"]) < 0.001)

# 2) 본문에 직접 적은 수치
abp = rev("Action Bass Plus")
abp_price = min(int(p["판매가"]) for p in P if "Action Bass Plus" in p["상품명"])
apj_price = min(int(p["판매가"]) for p in P if "Action PJ" in p["상품명"])
swing = rev("Jazz King")
hexr = rev("Hex B100")
all_sc = [int(r["평점"]) for r in R]
in_html("최저가 251,100원 (data-count)", f'data-count="{abp_price}"')
check("Action Bass Plus 가 20위권 최저가", abp_price == min(int(p["판매가"]) for p in P))
in_html("정가 349,000원", "349,000원")
in_html("평균 4.91", 'data-count="4.91"')
in_html("리뷰 23", 'data-count="23"')
five = round(100 * sum(int(r["평점"]) == 5 for r in abp) / len(abp))
in_html(f"5점 비율 {five}%", f'data-count="{five}" data-suffix="%"')
in_html("Hex 29/31", f"{sum(int(r['평점']) == 5 for r in hexr)}/{len(hexr)} 만점")
in_html("전체 평균", f"전체 평균 {sum(all_sc) / len(all_sc):.2f}점")
in_html("5점 152건", f"170건 중 {all_sc.count(5)}건이 5점")
recent = sum(r["작성일"] >= "2025" for r in R)
in_html(f"2025년 이후 {recent}건", f"2025년 이후에만 {recent}건")
since23 = round(100 * sum(r["작성일"] >= "2023" for r in R) / len(R))
in_html(f"2023년 이후 {since23}%", f"리뷰의 {since23}%가 2023년 이후")
in_html("Action Bass Plus 2025년 이후 4건", f"2025년 이후 리뷰 {sum(r['작성일'] >= '2025' for r in abp)}건도 모두 5점")
in_html("Hex 2025년 이후 10건", f"2025년 이후 리뷰가 {sum(r['작성일'] >= '2025' for r in hexr)}건")
in_html("가격차 7,900원", f"{apj_price - abp_price:,}원 싼 Action Bass Plus")
in_html("Swing 53건", f"<b>{len(swing)}</b><span>구매후기")
in_html("Swing 결함 7.5%", f"{100 * 4 / len(swing):.1f}%")
in_html("Swing 2점 존재", "2점 · 2023-03-30")
check("Swing 이 유일한 2점", [r["상품명"] for r in R if r["평점"] == "2"] == [r["상품명"] for r in swing if r["평점"] == "2"])
low = sorted({r["상품명"].split(" 베이스")[0] for r in R if int(r["평점"]) <= 3})
check("3점 이하 모델은 Swing·GB24JJ·Action PJ 뿐", all(any(k in n for k in ("Jazz King", "GB24JJ", "Action PJ")) for n in low), str(low))
sound = DATA["topics"][3]
in_html(f"소리 언급 {sound['n']}건", f"소리를 구체적으로 평가한 리뷰는 {sound['n']}건뿐")
subs_same = sum(r["성능"] == r["가격"] == r["디자인"] == r["배송"] == r["평점"] for r in R)
in_html(f"세부평점 {subs_same}건 동일", f"170건 중 {subs_same}건이 종합 평점과 같아")

# 3) 인용문이 실제 리뷰에 존재하는지
quotes = ["버징 개심하고 넥쪽에 찍힘", "교환받은 상품에도 기스가 있네요", "가방이 좋고 구성품도 많이",
          "처음부터 4현이 잘못 세팅되어", "뽑기가 잘 안 된것 같아요", "GB64JJ 가 미니멈", "바디 목재가 너무 약합니다",
          "너무이쁘고 소리도 좋아요 가선비짱짱", "마감이랑 긱백이 너무 좋아요", "치기도 편하고 소리가 명확하네요",
          "가격대 성능비가 최곱니다"]
for q in quotes:
    check(f"인용문 원문 존재: {q}", any(q.replace(" ", "") in r["내용"].replace(" ", "").replace("\n", "") for r in R))

print(f"\n{'ALL PASS' if not fails else f'{len(fails)} FAIL'}")
sys.exit(1 if fails else 0)
