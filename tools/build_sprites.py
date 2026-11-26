#!/usr/bin/env python3
"""sprites/*.txt (문자 격자) → 그림 파일 + 타이머용 글꼴 + 스위프트 목록 생성.

생성물 (전부 Generated/ 아래, 저장소에는 안 올림):
  Sprites/<스프라이트>_<프레임>.png        원본 크기 그림
  Fonts/PX<스프라이트><애니>.ttf          컬러 글꼴(sbix, 숫자 0~9 = 프레임)
  Fonts/PX<스프라이트><애니>L<n>.ttf      한 색짜리 글꼴 여러 겹(레이어 방식)
  Swift/SpriteCatalog.swift              글꼴 이름/색 목록
  App-Info.plist, Widget-Info.plist      UIAppFonts 가 채워진 설정 파일
  preview.png                            확인용 미리보기
"""
from __future__ import annotations

import io
import plistlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import newTable
from fontTools.ttLib.tables.sbixGlyph import Glyph as SbixGlyph
from fontTools.ttLib.tables.sbixStrike import Strike
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SPRITES = ROOT / "sprites"
OUT = ROOT / "Generated"
PIXEL_UNITS = 100          # 도트 한 칸 = 글꼴 단위 100
SBIX_SCALE = 8             # 컬러 글꼴에 넣는 그림 확대 배율 (흐려짐 방지)


# ---------------------------------------------------------------- 읽기
def load_palette() -> dict[str, tuple[int, int, int]]:
    pal = {}
    for line in (SPRITES / "palette.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ch, hexv, *_ = line.split()
        pal[ch] = tuple(int(hexv[i:i + 2], 16) for i in (0, 2, 4))
    return pal


@dataclass
class Sprite:
    name: str
    size: int = 20
    frames: dict[str, list[str]] = field(default_factory=dict)
    anims: dict[str, list[str]] = field(default_factory=dict)


def shift(grid, dx, dy, size):
    out = [["."] * size for _ in range(size)]
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            nx, ny = x + dx, y + dy
            if c != "." and 0 <= nx < size and 0 <= ny < size:
                out[ny][nx] = c
    return ["".join(r) for r in out]


def parse_sprite(path: Path, palette) -> Sprite:
    sp = Sprite(name=path.stem)
    lines = [l.rstrip() for l in path.read_text(encoding="utf-8").splitlines()]
    i = 0
    errors = []

    def take_grid(start):
        grid = []
        j = start
        while j < len(lines) and len(grid) < sp.size:
            l = lines[j]
            if l.startswith("@"):
                break
            if l.strip() == "" or l.startswith("#"):
                if grid:  # 그림 중간의 빈 줄은 끝으로 봄
                    break
                j += 1
                continue
            grid.append(l)
            j += 1
        return grid, j

    while i < len(lines):
        line = lines[i]
        if line.startswith("@size"):
            sp.size = int(line.split()[1])
            i += 1
        elif line.startswith("@frame"):
            parts = line.split()
            fname = parts[1]
            opts = dict(p.split("=", 1) for p in parts[2:])
            grid, j = take_grid(i + 1)
            if "base" in opts:
                base = sp.frames[opts["base"]]
                g = shift(base, int(opts.get("dx", 0)), int(opts.get("dy", 0)), sp.size)
                if "flash" in opts:
                    f = opts["flash"]
                    g = [re.sub(r"[^.]", f, r) for r in g]
                if grid:  # 덧칠
                    g = [list(r) for r in g]
                    for y, row in enumerate(grid):
                        for x, c in enumerate(row):
                            if c != ".":
                                g[y][x] = c
                    g = ["".join(r) for r in g]
                grid = g
            for y, row in enumerate(grid):
                if len(row) != sp.size:
                    errors.append(f"{path.name} [{fname}] {y}번째 줄 길이 {len(row)} (기대값 {sp.size})")
                for c in row:
                    if c != "." and c not in palette:
                        errors.append(f"{path.name} [{fname}] 팔레트에 없는 글자 '{c}'")
            if len(grid) != sp.size:
                errors.append(f"{path.name} [{fname}] 줄 수 {len(grid)} (기대값 {sp.size})")
            sp.frames[fname] = grid
            i = j
        elif line.startswith("@digits"):
            _, aname, *fr = line.split()
            for f in fr:
                if f not in sp.frames:
                    errors.append(f"{path.name} @digits {aname}: 없는 프레임 '{f}'")
            sp.anims[aname] = [fr[d % len(fr)] for d in range(10)]
            i += 1
        else:
            i += 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    return sp


# ---------------------------------------------------------------- 그림
def render(grid, palette, scale=1) -> Image.Image:
    n = len(grid)
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c != ".":
                px[x, y] = (*palette[c], 255)
    if scale != 1:
        img = img.resize((n * scale, n * scale), Image.NEAREST)
    return img


def png_bytes(img) -> bytes:
    b = io.BytesIO()
    img.save(b, "PNG")
    return b.getvalue()


# ---------------------------------------------------------------- 글꼴
GLYPHS = [".notdef", "space", "colon"] + [f"d{i}" for i in range(10)] + ["minus"]
CMAP = {0x20: "space", 0x3A: "colon", 0x2D: "minus", 0x2212: "minus",
        **{0x30 + i: f"d{i}" for i in range(10)}}


def base_font(ps_name: str, size: int):
    upm = size * PIXEL_UNITS
    fb = FontBuilder(upm, isTTF=True)
    fb.setupGlyphOrder(GLYPHS)
    fb.setupCharacterMap(CMAP)
    fb.setupHorizontalMetrics({g: (upm, 0) for g in GLYPHS})  # 모든 글자 폭 = 1em (고정폭)
    fb.setupHorizontalHeader(ascent=upm, descent=0)
    fb.setupNameTable({"familyName": ps_name, "styleName": "Regular",
                       "psName": ps_name, "fullName": ps_name})
    fb.setupOS2(sTypoAscender=upm, sTypoDescender=0, sTypoLineGap=0,
                usWinAscent=upm, usWinDescent=0, sxHeight=upm, sCapHeight=upm)
    fb.setupPost(isFixedPitch=1)
    return fb, upm


def outline_glyph(grid, color_ch, size):
    pen = TTGlyphPen(None)
    u = PIXEL_UNITS
    for y, row in enumerate(grid):
        x = 0
        while x < size:
            if row[x] == color_ch:
                x0 = x
                while x < size and row[x] == color_ch:
                    x += 1
                top, bot = (size - y) * u, (size - y - 1) * u
                pen.moveTo((x0 * u, top)); pen.lineTo((x * u, top))
                pen.lineTo((x * u, bot)); pen.lineTo((x0 * u, bot)); pen.closePath()
            else:
                x += 1
    return pen.glyph()


def empty_glyph():
    return TTGlyphPen(None).glyph()


def build_layer_font(ps_name, sp: Sprite, anim, color_ch, path):
    fb, _ = base_font(ps_name, sp.size)
    glyphs = {g: empty_glyph() for g in GLYPHS}
    for d in range(10):
        glyphs[f"d{d}"] = outline_glyph(sp.frames[anim[d]], color_ch, sp.size)
    fb.setupGlyf(glyphs)
    fb.save(str(path))


def build_color_font(ps_name, sp: Sprite, anim, palette, path):
    fb, _ = base_font(ps_name, sp.size)
    fb.setupGlyf({g: empty_glyph() for g in GLYPHS})
    sbix = newTable("sbix")
    sbix.version, sbix.flags = 1, 1
    ppem = sp.size * SBIX_SCALE
    strike = Strike(ppem=ppem, resolution=72)
    for d in range(10):
        name = f"d{d}"
        img = render(sp.frames[anim[d]], palette, SBIX_SCALE)
        strike.glyphs[name] = SbixGlyph(glyphName=name, graphicType="png ",
                                        originOffsetX=0, originOffsetY=0,
                                        imageData=png_bytes(img))
    sbix.strikes[ppem] = strike
    fb.font["sbix"] = sbix
    fb.save(str(path))


# ---------------------------------------------------------------- 스위프트
def camel(s):
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[_\-\s]", s) if p)


def lower_camel(s):
    c = camel(s)
    return c[:1].lower() + c[1:]


def main():
    palette = load_palette()
    sprites = [parse_sprite(p, palette) for p in sorted(SPRITES.glob("*.txt")) if p.stem != "palette"]

    for sub in ("Sprites", "Fonts", "Swift"):
        d = OUT / sub
        d.mkdir(parents=True, exist_ok=True)
        for f in d.iterdir():
            f.unlink()

    font_files = []
    swift_anims = []
    for sp in sprites:
        for fname, grid in sp.frames.items():
            render(grid, palette).save(OUT / "Sprites" / f"{sp.name}_{fname}.png")
        for aname, anim in sp.anims.items():
            base = f"PX{camel(sp.name)}{camel(aname)}"
            build_color_font(base, sp, anim, palette, OUT / "Fonts" / f"{base}.ttf")
            font_files.append(f"{base}.ttf")
            used = sorted({c for f in set(anim) for row in sp.frames[f] for c in row if c != "."})
            layers = []
            for n, ch in enumerate(used):
                lname = f"{base}L{n}"
                build_layer_font(lname, sp, anim, ch, OUT / "Fonts" / f"{lname}.ttf")
                font_files.append(f"{lname}.ttf")
                layers.append((lname, "%02x%02x%02x" % palette[ch]))
            swift_anims.append((sp, aname, base, layers))

    # 스위프트 목록
    lines = ["// 자동 생성 파일 — tools/build_sprites.py 가 만듦. 직접 고치지 말 것.",
             "import SwiftUI", "",
             "struct SpriteAnim: Hashable {",
             "    let sprite: String",
             "    let colorFont: String",
             "    let layers: [Layer]",
             "    let pixelSize: Int",
             "    let idleFrame: String",
             "    struct Layer: Hashable { let font: String; let hex: UInt32 }",
             "}", "",
             "enum SpriteCatalog {"]
    for sp, aname, base, layers in swift_anims:
        ls = ", ".join(f'.init(font: "{n}", hex: 0x{h})' for n, h in layers)
        idle = "idle" if "idle" in sp.frames else next(iter(sp.frames))
        lines.append(f'    static let {lower_camel(sp.name + "_" + aname)} = SpriteAnim('
                     f'sprite: "{sp.name}", colorFont: "{base}", layers: [{ls}], '
                     f'pixelSize: {sp.size}, idleFrame: "{sp.name}_{idle}")')
    lines.append("}")
    (OUT / "Swift" / "SpriteCatalog.swift").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 설정 파일에 글꼴 목록 넣기
    for name in ("App", "Widget"):
        with open(ROOT / "Config" / f"{name}-Info.plist", "rb") as f:
            pl = plistlib.load(f)
        pl["UIAppFonts"] = font_files
        with open(OUT / f"{name}-Info.plist", "wb") as f:
            plistlib.dump(pl, f)

    # 미리보기 (스프라이트별 한 줄: 모든 프레임 + 숫자 0~9 순서)
    scale, pad = 6, 6
    cell = 20 * scale + pad
    rows = sum(2 for _ in sprites)
    width = cell * 10 + pad
    sheet = Image.new("RGBA", (width, rows * cell + pad), (27, 31, 59, 255))
    y = pad
    for sp in sprites:
        for x, (fname, grid) in enumerate(sp.frames.items()):
            sheet.alpha_composite(render(grid, palette, scale * 20 // sp.size), (pad + x * cell, y))
        y += cell
        anim = sp.anims.get("battle") or next(iter(sp.anims.values()))
        for d in range(10):
            sheet.alpha_composite(render(sp.frames[anim[d]], palette, scale * 20 // sp.size), (pad + d * cell, y))
        y += cell
    sheet.save(OUT / "preview.png")
    print(f"스프라이트 {len(sprites)}개, 글꼴 {len(font_files)}개 생성 완료")


if __name__ == "__main__":
    main()
