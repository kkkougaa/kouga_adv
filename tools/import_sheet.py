#!/usr/bin/env python3
"""sprites/source/sheet.png (4x3 칸 도트 시트) → sprites/<이름>.txt 로 원본 그대로 옮기기.

시트 분석 결과: 도트 한 칸 = 7.5px, 전체 격자 기준점 x=6.5, y=4.5 (가장자리 주기 분석으로 측정).
각 도트 칸의 가운데 영역 색의 중앙값을 읽고, 압축 잡티로 생긴 비슷한 색은 하나로 합친다.
디자인(모양/색)은 바꾸지 않는다. 애니메이션 프레임은 원본을 옮기기/번쩍이기만 해서 만든다.
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "sprites" / "source" / "sheet.png"
PX, OX, OY = 7.5, 6.5, 4.5
CELL = 40            # 시트 한 칸 = 도트 40칸
TOP_CUT, BOTTOM_CUT = 4, 35   # 칸 안에서 "20x20" 글씨(위)와 이름 글씨(아래) 제외
CANVAS = 32          # 게임에서 쓰는 격자 크기
MERGE = 34           # 이 거리보다 가까운 색은 같은 색으로 봄

# (칸 x, 칸 y, 이름, 애니메이션 종류)
CELLS = [
    (0, 0, "player", "player"),
    (1, 0, "slime", "monster"),
    (2, 0, "goblin", "monster"),
    (3, 0, "bat", "monster"),
    (0, 1, "dragon", "monster"),
    (1, 1, "skull", "monster"),
    (2, 1, "skeleton", "monster"),
    (3, 1, "mushroom", "monster"),
    (0, 2, "eyeball", "monster"),
    (1, 2, "mummy", "monster"),
    (2, 2, "cactus", "monster"),
    (3, 2, "robot", "monster"),
]

CHARS = "ABCDEFGHIJLMNPQRSTUVWXYZabcdefghijklmnpqrstuvwxyz0123456789@$%&*+=?!<>^~"


def sample_sheet(img: np.ndarray) -> np.ndarray:
    h, w, _ = img.shape
    cols = int((w - OX) // PX)
    rows = int((h - OY) // PX)
    out = np.zeros((rows, cols, 3), dtype=int)
    for r in range(rows):
        for c in range(cols):
            x0, y0 = OX + c * PX, OY + r * PX
            block = img[int(y0 + 2):int(y0 + PX - 1), int(x0 + 2):int(x0 + PX - 1)].reshape(-1, 3)
            out[r, c] = np.median(block, axis=0)
    return out


def is_bg(c) -> bool:
    mx, mn = max(c), min(c)
    return mx < 45   # 검정 (격자선은 도트 칸 경계에 있어서 가운데 읽기로 이미 피함)


def extract(grid: np.ndarray, cx: int, cy: int):
    cell = grid[cy * CELL + TOP_CUT: cy * CELL + BOTTOM_CUT, cx * CELL: (cx + 1) * CELL]
    h, w, _ = cell.shape
    bg = np.zeros((h, w), bool)
    q = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while q:
        x, y = q.popleft()
        if 0 <= x < w and 0 <= y < h and not bg[y, x] and is_bg(cell[y, x]):
            bg[y, x] = True
            q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return cell, ~bg


def cluster(colors: list[tuple[int, int, int]]):
    """빈도 높은 색부터 대표색으로 잡고 가까운 색을 합침"""
    from collections import Counter
    cnt = Counter(colors)
    reps: list[list] = []   # [합계r,g,b, 개수]
    assign = {}
    for col, n in cnt.most_common():
        best, bd = None, 1e9
        for i, rp in enumerate(reps):
            cen = (rp[0] / rp[3], rp[1] / rp[3], rp[2] / rp[3])
            d = sum((a - b) ** 2 for a, b in zip(col, cen)) ** 0.5
            if d < bd:
                best, bd = i, d
        if best is not None and bd < MERGE:
            rp = reps[best]
            rp[0] += col[0] * n; rp[1] += col[1] * n; rp[2] += col[2] * n; rp[3] += n
            assign[col] = best
        else:
            reps.append([col[0] * n, col[1] * n, col[2] * n, n])
            assign[col] = len(reps) - 1
    centers = [tuple(int(round(v / rp[3])) for v in rp[:3]) for rp in reps]
    return {c: centers[i] for c, i in assign.items()}


TEMPLATES = {
    "player": """
@frame windup base=idle dx=-1
@frame slash base=idle dx=1
@frame hit base=idle flash={white}

# 공격 주기 2초: 짝수 초 = 베기, 홀수 초 = 준비
@digits battle slash windup
""",
    "monster": """
@frame bob base=idle dy=-1
@frame hit base=idle flash={white}

# 짝수 초 = 맞아서 하얗게 번쩍, 홀수 초 = 통통
@digits battle hit idle hit bob hit idle hit bob hit idle
""",
}


def main():
    img = np.asarray(Image.open(SHEET).convert("RGB")).astype(int)
    grid = sample_sheet(img)

    sprites = []
    all_colors = []
    for cx, cy, name, kind in CELLS:
        cell, fg = extract(grid, cx, cy)
        ys, xs = np.nonzero(fg)
        cell = cell[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        fg = fg[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        sprites.append((name, kind, cell, fg))
        all_colors += [tuple(int(v) for v in cell[y, x]) for y, x in zip(*np.nonzero(fg))]

    mapping = cluster(all_colors)
    centers = sorted(set(mapping.values()), key=lambda c: -sum(c))
    if len(centers) > len(CHARS):
        sys.exit(f"색이 너무 많아 ({len(centers)})")
    char_of = {c: CHARS[i] for i, c in enumerate(centers)}
    white = char_of[max(centers, key=lambda c: min(c))]

    pal_lines = ["# 팔레트: tools/import_sheet.py 가 sprites/source/sheet.png 에서 뽑음",
                 "# 형식: <글자> <RRGGBB>", "# '.' 는 투명"]
    pal_lines += [f"{char_of[c]} {'%02x%02x%02x' % c}" for c in centers]
    (ROOT / "sprites" / "palette.txt").write_text("\n".join(pal_lines) + "\n", encoding="utf-8")

    for name, kind, cell, fg in sprites:
        h, w = fg.shape
        if h > CANVAS or w > CANVAS:
            sys.exit(f"{name}: {w}x{h} 가 격자 {CANVAS} 보다 큼")
        offx, offy = (CANVAS - w) // 2, CANVAS - h
        rows = [["."] * CANVAS for _ in range(CANVAS)]
        for y in range(h):
            for x in range(w):
                if fg[y, x]:
                    rows[offy + y][offx + x] = char_of[mapping[tuple(int(v) for v in cell[y, x])]]
        text = "\n".join("".join(r) for r in rows)
        body = (f"# {name} — 원본: sprites/source/sheet.png (tools/import_sheet.py 로 자동 변환, {w}x{h})\n"
                f"@size {CANVAS}\n\n@frame idle\n{text}\n" + TEMPLATES[kind].format(white=white))
        (ROOT / "sprites" / f"{name}.txt").write_text(body, encoding="utf-8")
        print(f"{name}: {w}x{h}")
    print(f"색 {len(centers)}개")


if __name__ == "__main__":
    main()
