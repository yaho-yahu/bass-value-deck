"""manim 설명 애니메이션 -> assets/video/*.mp4
실행: .venv-manim/Scripts/python -m manim -r 1600,900 --fps 30 scripts/scenes.py Funnel ValueIndex
"""
import json
from pathlib import Path

from manim import (DOWN, LEFT, RIGHT, UP, Create, FadeIn, GrowFromEdge, LaggedStart, Line,
                   RoundedRectangle, Scene, Text, Transform, VGroup, Write, config)

DATA = json.loads((Path(__file__).resolve().parents[1] / "data" / "models.json").read_text(encoding="utf-8"))
BG, INK, INK2, INK3 = "#10131a", "#eef1f5", "#aab2c0", "#6f7887"
BLUE, AMBER, GRAY = "#3987e5", "#f2b544", "#4a515d"
FONT = "Malgun Gothic"
config.background_color = BG


def T(s, size=30, color=INK, weight="NORMAL"):
    return Text(s, font=FONT, font_size=size, color=color, weight=weight)


class Funnel(Scene):
    def construct(self):
        t = DATA["totals"]
        steps = [
            (t["ranked"], "판매순위", "2026 연간 · 베이스기타"),
            (t["products"], "상품", "구성품 패키지 1개 제외"),
            (t["models"], "모델", "색상 옵션을 하나로"),
            (t["reviews"], "구매후기", "사이트 표시 건수와 100% 일치"),
        ]
        widths = [8.6, 7.2, 5.8, 4.4]
        rows = VGroup()
        for i, ((num, label, note), w) in enumerate(zip(steps, widths)):
            last = i == len(steps) - 1
            box = RoundedRectangle(width=w, height=1.25, corner_radius=0.18,
                                   fill_color=AMBER if last else BLUE, fill_opacity=0.95 if last else 0.22 + i * 0.18,
                                   stroke_width=0)
            n = T(f"{num}", 46, "#10131a" if last else INK, "BOLD")
            lab = T(label, 28, "#10131a" if last else INK)
            head = VGroup(n, lab).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
            head.move_to(box)
            side = T(note, 22, INK2)
            side.next_to(box, RIGHT, buff=0.45)
            rows.add(VGroup(box, head, side))
        rows.arrange(DOWN, buff=0.32)
        for row in rows:
            row[0].set_x(-2.4)
            row[1].move_to(row[0])
            row[2].move_to([2.55, row[0].get_y(), 0], aligned_edge=LEFT)
        rows.move_to([rows.get_center()[0], 0, 0])
        for i, row in enumerate(rows):
            self.play(GrowFromEdge(row[0], LEFT), run_time=0.55)
            self.play(FadeIn(row[1], shift=UP * 0.2), FadeIn(row[2], shift=LEFT * 0.2), run_time=0.45)
            if i < len(rows) - 1:
                self.wait(0.15)
        self.wait(2.5)


class ValueIndex(Scene):
    def construct(self):
        models = DATA["models"]
        title = T("가성비 지수 = 보정 평점 ÷ 판매가(10만원)", 34, INK, "BOLD").to_edge(UP, buff=0.55)
        sub = T("보정 평점: 리뷰가 적은 모델은 전체 평균(4.8점) 쪽으로 당겨 계산", 22, INK3).next_to(title, DOWN, buff=0.22)
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.5)

        vmax = 2.1
        scale = 8.2 / vmax
        x0 = -3.1
        row_h = 0.47

        def build(order):
            g = VGroup()
            for i, m in enumerate(order):
                y = 1.45 - i * row_h
                top = m["key"] == "abp"
                bar = RoundedRectangle(width=max(m["value"] * scale, 0.05), height=0.36, corner_radius=0.06,
                                       fill_color=AMBER if top else BLUE, fill_opacity=1 if top else 0.75,
                                       stroke_width=0)
                bar.move_to([x0 + bar.width / 2, y, 0])
                name = T(m["name"], 21, INK if top else INK2).move_to([x0 - 0.25, y, 0], aligned_edge=RIGHT)
                val = T(f"{m['value']:.2f}", 21, AMBER if top else INK).next_to(bar, RIGHT, buff=0.18)
                g.add(VGroup(name, bar, val))
            return g

        by_price = sorted(models, key=lambda m: m["price"])
        by_value = sorted(models, key=lambda m: -m["value"])
        axis = Line([x0, 1.75, 0], [x0, 1.45 - 9 * row_h - 0.3, 0], color=GRAY, stroke_width=2)
        start = build(by_price)
        self.play(Create(axis), run_time=0.4)
        self.play(LaggedStart(*[GrowFromEdge(r[1], LEFT) for r in start], lag_ratio=0.12),
                  LaggedStart(*[FadeIn(r[0]) for r in start], lag_ratio=0.12), run_time=1.8)
        self.play(LaggedStart(*[FadeIn(r[2]) for r in start], lag_ratio=0.08), run_time=0.8)
        self.wait(0.6)
        end = build(by_value)
        mapping = {m["key"]: i for i, m in enumerate(by_value)}
        self.play(*[Transform(start[i], end[mapping[m["key"]]]) for i, m in enumerate(by_price)], run_time=1.4)
        note = T("평점이 4.7~5.0에 몰려 있어 가격 차이가 순위를 가른다", 22, INK2).to_edge(DOWN, buff=0.32)
        self.play(FadeIn(note, shift=UP * 0.2), run_time=0.6)
        self.wait(2.5)
