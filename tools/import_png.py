#!/usr/bin/env python3
"""도트 그림(확대된 그림/시트 칸 포함) → sprites/*.txt 문자 격자로 그대로 옮기기.

사용 예:
  # 시트에서 칸 하나 잘라서 (칸 좌표: 가로 칸 번호, 세로 칸 번호, 칸 수 4x3)
  python3 tools/import_png.py 시트.png --name player --cell 0 0 --grid 4 3
  # 이미 잘라둔 그림 한 장
  python3 tools/import_png.py player.png --name player

동작:
  1. 칸 아래쪽 글씨 영역은 잘라냄(--label-cut 비율)
  2. 배경(가장자리와 이어진 어두운 색)을 찾아 그림 영역을 찾음
  3. 도트 한 칸 크기를 추정해서(또는 --px 로 직접 지정) 칸 가운데 색을 읽음
  4. 색을 팔레트 글자로 바꿈. 팔레트에 없는 색은 새 글자를 만들어 palette.txt 에 추가
  5. 배경과 같은 검정 외곽선은 그림 둘레에 'o' 로 다시 둘러줌(--no-outline 으로 끔)
원본 디자인을 바꾸지 않는 게 목적이라 색 보정/수정은 하지 않음.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PALETTE = ROOT / "sprites" / "palette.txt"
SPARE = "ACDEFHIJMOPQUVXZacdefijkmquvxz0123456789@$%&*+=?!"


def is_dark(c, th):
    return max(c[:3]) <= th


def estimate_px(img, box, bgmask):
    """같은 색이 이어진 길이들의 최빈값 계열로 도트 한 칸 크기 추정"""
    x0, y0, x1, y1 = box
    runs = Counter()
    px = img.load()
    for y in range(y0, y1, 2):
        run, prev = 0, None
        for x in range(x0, x1):
            c = px[x, y][:3]
            if prev is not None and sum(abs(a - b) for a, b in zip(c, prev)) < 40:
                run += 1
            else:
                if run >= 3:
                    runs[run] += 1
                run = 1
            prev = c
    if not runs:
        return None
    # 작은 쪽 최빈 길이 = 한 칸
    common = [r for r, _ in runs.most_common(8)]
    return min(common)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--name", required=True)
    ap.add_argument("--size", type=int, default=20, help="도트 격자 크기")
    ap.add_argument("--cell", type=int, nargs=2, metavar=("X", "Y"))
    ap.add_argument("--grid", type=int, nargs=2, metavar=("COLS", "ROWS"), default=(4, 3))
    ap.add_argument("--label-cut", type=float, default=0.15, help="칸 아래에서 잘라낼 글씨 영역 비율")
    ap.add_argument("--px", type=float, help="도트 한 칸의 픽셀 크기 (자동 추정 대신)")
    ap.add_argument("--dark", type=int, default=40, help="이 값 이하 밝기는 검정(배경/외곽선)")
    ap.add_argument("--no-outline", action="store_true")
    ap.add_argument("--outline8", action="store_true", help="외곽선을 대각선 칸까지 두름")
    ap.add_argument("--frame", default="idle")
    args = ap.parse_args()

    img = Image.open(args.image).convert("RGBA")
    if args.cell:
        cw, ch = img.width / args.grid[0], img.height / args.grid[1]
        cx, cy = args.cell
        img = img.crop((int(cx * cw), int(cy * ch), int((cx + 1) * cw), int((cy + 1) * ch - ch * args.label_cut)))

    W, H = img.size
    px = img.load()
    # 가장자리와 이어진 어두운/회색(격자선) 영역 = 배경
    def bgish(c):
        r, g, b = c[:3]
        return c[3] < 128 or is_dark(c, args.dark) or (abs(r - g) < 18 and abs(g - b) < 18 and max(r, g, b) < 110)
    bg = [[False] * W for _ in range(H)]
    q = deque((x, y) for x in range(W) for y in (0, H - 1)) + deque((x, y) for y in range(H) for x in (0, W - 1))
    while q:
        x, y = q.popleft()
        if not (0 <= x < W and 0 <= y < H) or bg[y][x] or not bgish(px[x, y]):
            continue
        bg[y][x] = True
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    xs = [x for y in range(H) for x in range(W) if not bg[y][x]]
    ys = [y for y in range(H) for x in range(W) if not bg[y][x]]
    if not xs:
        raise SystemExit("그림을 못 찾았어")
    box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
    p = args.px or estimate_px(img, box, bg)
    if not p:
        raise SystemExit("도트 크기 추정 실패 → --px 로 지정해줘")
    cols = round((box[2] - box[0]) / p)
    rows = round((box[3] - box[1]) / p)
    print(f"그림 영역 {box}, 도트 한 칸 ≈ {p:.2f}px, 그림 {cols}x{rows}칸")
    if cols > args.size or rows > args.size:
        raise SystemExit(f"격자({args.size})보다 큼 → --px 를 크게 지정해줘")

    # 팔레트
    pal = {}
    lines = PALETTE.read_text(encoding="utf-8").splitlines()
    for l in lines:
        s = l.strip()
        if s and not s.startswith("#"):
            k, h, *_ = s.split()
            pal[k] = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    added = []

    def to_char(c):
        best = min(pal.items(), key=lambda kv: sum((a - b) ** 2 for a, b in zip(kv[1], c)))
        if sum((a - b) ** 2 for a, b in zip(best[1], c)) <= 12 ** 2 * 3:
            return best[0]
        k = next(ch for ch in SPARE if ch not in pal)
        pal[k] = c
        added.append(f"{k} {'%02x%02x%02x' % c} {args.name}에서 가져옴")
        return k

    # 아래쪽 가운데 정렬로 격자에 배치
    offx = (args.size - cols) // 2
    offy = args.size - rows
    grid = [["."] * args.size for _ in range(args.size)]
    for r in range(rows):
        for c in range(cols):
            sx = int(box[0] + (c + 0.5) * p)
            sy = int(box[1] + (r + 0.5) * p)
            if bg[min(sy, H - 1)][min(sx, W - 1)]:
                continue
            col = px[min(sx, W - 1), min(sy, H - 1)]
            grid[offy + r][offx + c] = "K" if is_dark(col, args.dark) and "K" in pal else to_char(col[:3])

    if not args.no_outline:
        snap = [row[:] for row in grid]
        for y in range(args.size):
            for x in range(args.size):
                if snap[y][x] == "." and any(
                    0 <= x + dx < args.size and 0 <= y + dy < args.size and snap[y + dy][x + dx] != "."
                    for dx, dy in (((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (1, -1), (-1, 1), (-1, -1)) if args.outline8 else ()))):
                    grid[y][x] = "o"

    if added:
        with PALETTE.open("a", encoding="utf-8") as f:
            f.write("\n".join(added) + "\n")
        print("팔레트에 추가:", ", ".join(a.split()[0] for a in added))

    text = "\n".join("".join(r) for r in grid)
    out = ROOT / "sprites" / "imported" / f"{args.name}.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text(f"@size {args.size}\n\n@frame {args.frame}\n{text}\n", encoding="utf-8")
    print(text)
    print(f"→ {out.relative_to(ROOT)} (확인 후 원래 파일의 @frame {args.frame} 부분에 붙여넣기)")


if __name__ == "__main__":
    main()
