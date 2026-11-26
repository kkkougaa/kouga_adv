#!/usr/bin/env python3
"""전투 이펙트 도트를 그려서 sprites/fx.txt 와 sprites/palette_fx.txt 로 저장.

캐릭터/몬스터 도트와는 따로 있는 그림이고, 화면에서 몬스터 위에 겹쳐 그린다.
모양을 바꾸고 싶으면 이 파일의 숫자를 고치거나, 만들어진 fx.txt 를 직접 고쳐도 됨
(직접 고쳤으면 이 스크립트를 다시 돌리지 말 것).
"""
from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
N = 32

# 이펙트 전용 색 (캐릭터 팔레트 글자와 안 겹치는 기호)
PAL = {
    "[": "ffffff",  # 하양
    "]": "fff6b0",  # 연노랑
    "{": "ffd23f",  # 노랑
    "}": "ff8a2a",  # 주황
    "|": "e8432e",  # 빨강
    "/": "7af0e4",  # 밝은 청록 (주인공 머리색 계열)
    ";": "2ec4b6",  # 청록
    ",": "c9c3d6",  # 연기
    "`": "8a829e",  # 진한 연기
    "'": "b8860b",  # 동전 그림자
}


def blank():
    return [["."] * N for _ in range(N)]


def put(g, x, y, c, only_empty=False):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < N and 0 <= y < N and (not only_empty or g[y][x] == "."):
        g[y][x] = c


def arc(g, cx, cy, r, a0, a1, width, core, edge):
    """초승달 모양 칼 궤적: 가운데가 두껍고 양 끝이 가늘어짐"""
    for y in range(N):
        for x in range(N):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx)) % 360
            span = (a - a0) % 360
            total = (a1 - a0) % 360
            if span > total:
                continue
            t = span / total
            w = width * math.sin(math.pi * t) + 0.6
            if r - w <= d <= r:
                g[y][x] = core if d >= r - w * 0.55 else edge


def star(g, cx, cy, size, colors):
    """4방향 반짝임. colors = 가운데부터 바깥 순서"""
    for i in range(-size, size + 1):
        k = abs(i)
        c = colors[min(len(colors) - 1, k * len(colors) // (size + 1))]
        put(g, cx + i, cy, c)
        put(g, cx, cy + i, c)
    for i in range(-(size // 2), size // 2 + 1):
        k = abs(i)
        c = colors[min(len(colors) - 1, 1 + k * (len(colors) - 1) // (size // 2 + 1))]
        put(g, cx + i, cy + i, c, only_empty=True)
        put(g, cx + i, cy - i, c, only_empty=True)
    put(g, cx, cy, colors[0])


def ring(g, cx, cy, r, w, c, gaps=0):
    for y in range(N):
        for x in range(N):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if r - w <= d <= r:
                if gaps:
                    a = math.degrees(math.atan2(y - cy, x - cx)) % 360
                    if int(a // (360 / gaps)) % 2:
                        continue
                g[y][x] = c


def disc(g, cx, cy, r, c):
    for y in range(N):
        for x in range(N):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                g[y][x] = c


def frames():
    out = {}
    # 일반 타격: 대각선 베기 + 작은 불꽃
    g = blank()
    arc(g, 30, 2, 24, 95, 175, 2.6, "[", ";")
    star(g, 17, 18, 4, ["[", "]", "{", "}"])
    out["hit"] = g

    # 강타: X자 베기 + 큰 노란 불꽃
    g = blank()
    # 강타 때는 몬스터가 하얗게 번쩍이니까 궤적은 진한 색으로
    arc(g, 31, 1, 25, 95, 175, 3.2, ";", "/")
    arc(g, 1, 1, 25, 5, 85, 3.2, ";", "/")
    star(g, 16, 17, 7, ["|", "}", "{", "{", "}", "|"])
    out["crit"] = g

    # 스킬 폭발 3프레임
    g = blank()
    disc(g, 16, 19, 4.5, "{"); disc(g, 16, 19, 2.5, "["); star(g, 16, 19, 6, ["[", "]", "{", "}"])
    out["boom1"] = g
    g = blank()
    disc(g, 16, 19, 9, "}"); disc(g, 16, 19, 6.5, "{"); disc(g, 16, 19, 3.5, "]")
    ring(g, 16, 19, 12.5, 1.3, "|", gaps=12)
    out["boom2"] = g
    g = blank()
    ring(g, 16, 19, 13, 2.2, ",", gaps=10); ring(g, 16, 19, 9, 1.5, "`", gaps=8)
    star(g, 6, 9, 2, ["]", "{"]); star(g, 26, 10, 2, ["]", "{"]); star(g, 24, 27, 1, ["]", "{"])
    out["boom3"] = g

    # 처치: 연기 + 동전
    g = blank()
    for cx, cy, r in ((11, 22, 5), (19, 21, 6), (15, 16, 5), (23, 25, 4), (8, 26, 3.5)):
        disc(g, cx, cy, r, ",")
    for cx, cy, r in ((12, 24, 2.2), (20, 23, 3), (16, 18, 2)):
        disc(g, cx, cy, r, "`")
    disc(g, 24, 9, 4, "'"); disc(g, 23.5, 8.5, 3.4, "{"); put(g, 22, 7, "]"); put(g, 23, 7, "]")
    for y in range(7, 11):
        put(g, 24, y, "'")
    star(g, 29, 4, 1, ["[", "]"])
    out["poof"] = g
    return out


def main():
    fr = frames()
    lines = ["# 전투 이펙트 — tools/draw_effects.py 가 그림. 몬스터 위에 겹쳐서 보여줌.",
             "# '-' 는 빈 프레임(아무것도 안 보임)", f"@size {N}", ""]
    for name, g in fr.items():
        lines.append(f"@frame {name}")
        lines += ["".join(r) for r in g]
        lines.append("")
    lines += [
        "# 타격: 짝수 초마다 베기, 0초(5번째 공격)는 강타",
        "@digits hit crit - hit - hit - hit - hit -",
        "# 스킬: 3초 거꾸로 세는 타이머의 3,2,1 에 폭발, 0 은 비움",
        "@digits skill - boom3 boom2 boom1 - - - - - -",
    ]
    (ROOT / "sprites" / "fx.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    pal = ["# 이펙트 전용 색 — tools/draw_effects.py"] + [f"{k} {v}" for k, v in PAL.items()]
    (ROOT / "sprites" / "palette_fx.txt").write_text("\n".join(pal) + "\n", encoding="utf-8")
    print("이펙트", ", ".join(fr))


if __name__ == "__main__":
    main()
