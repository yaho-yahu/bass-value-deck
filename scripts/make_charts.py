"""matplotlib 정적 차트 -> assets/charts/*.svg (덱 팔레트, 투명 배경, 글자는 path로 내장)"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BASE = Path(__file__).resolve().parents[1]
DATA = json.loads((BASE / "data" / "models.json").read_text(encoding="utf-8"))
OUT = BASE / "assets" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

INK, INK2, INK3, LINE = "#eef1f5", "#aab2c0", "#6f7887", "#2a303c"
BLUE, BLUE_L, YELLOW, RED, GRAY, AMBER = "#3987e5", "#86b6ef", "#c98500", "#e66767", "#4a515d", "#f2b544"

plt.rcParams.update({
    "font.family": "Malgun Gothic", "svg.fonttype": "path", "axes.unicode_minus": False,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK3, "ytick.color": INK2,
    "axes.edgecolor": LINE, "font.size": 15, "axes.facecolor": "none", "figure.facecolor": "none",
})


def save(fig, name):
    fig.savefig(OUT / f"{name}.svg", transparent=True, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("saved", name)


def rating_distribution():
    models = sorted(DATA["models"], key=lambda m: (m["dist"][0] / m["n"], m["n"]))
    fig, ax = plt.subplots(figsize=(10.5, 6.4))
    colors = [BLUE, BLUE_L, YELLOW, RED, RED]
    labels = ["5점", "4점", "3점", "2점", "1점"]
    for i, m in enumerate(models):
        left = 0
        for s, cnt in enumerate(m["dist"]):
            if not cnt:
                continue
            w = cnt / m["n"] * 100
            ax.barh(i, w - 0.35, left=left, height=0.62, color=colors[s], edgecolor="none")
            if w >= 7:
                ax.text(left + w / 2, i, str(cnt), ha="center", va="center", fontsize=15,
                        color="#0b1220" if s in (0, 1) else INK, fontweight="bold")
            left += w
        ax.text(101.5, i, f"{m['n']}건 · {m['avg']:.2f}", va="center", fontsize=16, color=INK2)
    ax.set_yticks(range(len(models)), [m["name"] for m in models], fontsize=17, color=INK)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.tick_params(length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=LINE, lw=1)
    ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors[:4]]
    ax.legend(handles, labels[:4], ncol=4, loc="lower left", bbox_to_anchor=(0, 1.01),
              frameon=False, fontsize=16, handlelength=1, labelcolor=INK2)
    save(fig, "rating_dist")


def years():
    ys = DATA["years"]
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    xs = [y["year"] for y in ys]
    ns = [y["n"] for y in ys]
    cols = [BLUE if int(y) >= 2023 else GRAY for y in xs]
    bars = ax.bar(xs, ns, color=cols, width=0.68)
    for b, n, y in zip(bars, ns, xs):
        ax.text(b.get_x() + b.get_width() / 2, n + 1.2, str(n), ha="center", fontsize=17,
                color=INK if int(y) >= 2023 else INK2)
    ax.text(10, 24 + 7.5, "10월 2일까지", ha="center", fontsize=14, color=INK3)
    ax.annotate("", xy=(6.6, 58), xytext=(10.4, 58),
                arrowprops=dict(arrowstyle="-", color=AMBER, lw=1.6))
    ax.text(8.5, 60.5, f"2023년 이후 {DATA['totals']['since_2023_pct']}%", ha="center", fontsize=19,
            color=AMBER, fontweight="bold")
    ax.set_ylim(0, 66)
    ax.set_yticks([0, 20, 40, 60])
    ax.tick_params(length=0, labelsize=16)
    ax.tick_params(axis="x", colors=INK2)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=LINE, lw=1)
    ax.set_axisbelow(True)
    save(fig, "years")


def waffles():
    keys = ["swing", "apj", "gb24", "bb", "hex", "abp"]
    models = {m["key"]: m for m in DATA["models"]}
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.6))
    for ax, key in zip(axes.flat, keys):
        m = models[key]
        cols = 10
        rows = -(-m["n"] // cols)
        for i in range(m["n"]):
            r, c = divmod(i, cols)
            bad = i < m["defects"]
            color = (AMBER if key == "bb" else RED) if bad else ("#2c4a72" if m["defects"] else BLUE)
            ax.add_patch(FancyBboxPatch((c, -r), 0.78, 0.78, boxstyle="round,pad=0,rounding_size=0.14",
                                        color=color, lw=0))
        ax.set_xlim(-0.2, 10)
        ax.set_ylim(-5.4, 1.2)
        ax.set_aspect("equal")
        ax.axis("off")
        rate = f"{m['defects']}/{m['n']}건"
        ax.text(0, 1.55, m["name"], fontsize=17, color=INK, fontweight="bold", va="bottom")
        ax.text(10, 1.55, rate, fontsize=17, ha="right", va="bottom",
                color=(AMBER if key == "bb" else RED) if m["defects"] else BLUE)
    fig.subplots_adjust(hspace=0.55, wspace=0.18)
    save(fig, "waffle")


if __name__ == "__main__":
    rating_distribution()
    years()
    waffles()
