#!/usr/bin/env python3
"""Build the aay brand kit: outlined SVGs plus every PNG/ICO size, all rendered from the SVGs.

    pip install fonttools resvg-py pillow
    python build_brand.py [OUT_DIR] [--font PATH_TO_Inter_28pt-Black.ttf]

Everything is driven by MONOGRAM / WORDMARK / COLORS below; edit, re-run, done.
Text is converted to outlines, so the SVGs need no font installed to view or edit.
"""
import argparse
import io
import math
import os
import sys

import resvg_py
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from fontTools.ttLib import TTFont
from PIL import Image

# --------------------------------------------------------------------------- design
COLORS = dict(
    bg_top="#161B22",      # GitHub dark canvas-subtle
    bg_bottom="#0D1117",   # GitHub dark canvas
    fg="#FFFFFF",
    accent="#58A6FF",      # GitHub blue
    ink_dark="#0D1117",    # letters on light backgrounds
)
MONOGRAM = dict(text="a", track=-0.09, width=0.58, slant=6,
                dot_size=0.42, dot_gap=0.02, dot_dip=0.30, center_y=0.45)
WORDMARK = dict(text="aay", track=-0.09, width=0.74, slant=6,
                dot_size=0.52, dot_gap=0.02, dot_dip=0.30, center_y=0.45)
RADIUS = 0.235             # tile corner radius, fraction of tile size
DEFAULT_FONT = r"C:\Windows\Fonts\Inter_28pt-Black.ttf"   # Inter Display Black (OFL)


# --------------------------------------------------------------------------- geometry
class Font:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.hmtx = self.tt["hmtx"]
        self.xh = self.bounds("x")[3]

    def name(self, ch):
        return self.cmap[ord(ch)]

    def bounds(self, ch):
        bp = BoundsPen(self.gs)
        self.gs[self.name(ch)].draw(bp)
        return bp.bounds


def mark_geometry(font, spec, W, H, width_frac=None):
    """Return (path_d, (cx, cy, r), ink_bounds) for spec laid out on a W x H canvas."""
    p = dict(spec)
    k = math.tan(math.radians(p["slant"]))
    xs, x = [], 0.0
    for ch in p["text"]:
        xs.append(x)
        x += font.hmtx[font.name(ch)][0] + p["track"] * font.upm
    # Measure by advance width (side bearings included), not ink: this is the spacing
    # the approved design was drawn with, and it keeps the dot's gap consistent.
    b = [font.bounds(ch) for ch in p["text"]]
    adv = [font.hmtx[font.name(ch)][0] for ch in p["text"]]
    left = min(0, min(xo + bb[0] for xo, bb in zip(xs, b)))
    right = max(xo + max(a, bb[2]) for xo, a, bb in zip(xs, adv, b))
    xh = font.xh
    # px-per-unit so that letters + gap + dot + slant overhang span width_frac of W
    span_units = (right - left) + xh * p["dot_size"] * (1 + p["dot_gap"]) + k * xh * 0.5
    s = (width_frac or p["width"]) * W / span_units
    dot = xh * s * p["dot_size"]
    gap = dot * p["dot_gap"]
    total = span_units * s
    ox = (W - total) / 2 - left * s
    base = H * p["center_y"] + xh * s / 2           # baseline (SVG y grows downward)
    pivot = H / 2                                    # slant pivot

    pen = SVGPathPen(font.gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    bpen = BoundsPen(font.gs)
    for ch, xo in zip(p["text"], xs):
        a = ox + xo * s
        t = Transform(s, 0, k * s, -s, a - k * base + k * pivot, base)
        font.gs[font.name(ch)].draw(TransformPen(pen, t))
        font.gs[font.name(ch)].draw(TransformPen(bpen, t))
    x0 = ox + right * s + gap
    top, bottom = base - dot * (1 - p["dot_dip"]), base + dot * p["dot_dip"]
    cy = (top + bottom) / 2
    cx = x0 + dot / 2 - k * (cy - pivot)
    r = dot / 2
    gx0, gy0, gx1, gy1 = bpen.bounds
    ink = (min(gx0, cx - r), min(gy0, cy - r), max(gx1, cx + r), max(gy1, cy + r))
    return pen.getCommands(), (cx, cy, r), ink


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def defs():
    return (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{COLORS["bg_top"]}"/>'
            f'<stop offset="1" stop-color="{COLORS["bg_bottom"]}"/></linearGradient></defs>')


def svg_doc(W, H, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(W)}" height="{fmt(H)}" '
            f'viewBox="0 0 {fmt(W)} {fmt(H)}"><title>{title}</title>{body}</svg>\n')


def mark_body(font, spec, W, H, fg, width_frac=None, dx=0.0, dy=0.0):
    d, (cx, cy, r), ink = mark_geometry(font, spec, W, H, width_frac)
    g = f'<g transform="translate({fmt(dx)} {fmt(dy)})">' if (dx or dy) else "<g>"
    return (f'{g}<path id="letters" fill="{fg}" d="{d}"/>'
            f'<circle id="dot" cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="{COLORS["accent"]}"/></g>'), ink


def tile(font, spec, S=1024, shape="rounded", title="aay"):
    bg = {"rounded": f'<rect width="{S}" height="{S}" rx="{fmt(RADIUS * S)}" fill="url(#bg)"/>',
          "square": f'<rect width="{S}" height="{S}" fill="url(#bg)"/>',
          "circle": f'<circle cx="{S / 2}" cy="{S / 2}" r="{S / 2}" fill="url(#bg)"/>'}[shape]
    body, _ = mark_body(font, spec, S, S, COLORS["fg"])
    return svg_doc(S, S, defs() + bg + body, title)


def transparent(font, spec, fg, title, pad=0.08):
    """Letters + dot only, cropped to the ink with a little padding."""
    S = 1024
    _, _, (x0, y0, x1, y1) = mark_geometry(font, spec, S, S)
    h = y1 - y0
    p = h * pad
    W, H = (x1 - x0) + 2 * p, h + 2 * p
    body, _ = mark_body(font, spec, S, S, fg, dx=p - x0, dy=p - y0)
    return svg_doc(W, H, body, title)


def banner(font, spec, W=1280, H=640, title="aay"):
    body, _ = mark_body(font, {**spec, "center_y": 0.47}, W, H, COLORS["fg"], width_frac=0.44)
    return svg_doc(W, H, defs() + f'<rect width="{W}" height="{H}" fill="url(#bg)"/>' + body, title)


# --------------------------------------------------------------------------- output
def png(svg, path, w=None, h=None):
    data = resvg_py.svg_to_bytes(svg_string=svg, width=w, height=h, skip_system_fonts=True)
    with open(path, "wb") as f:
        f.write(bytes(data))
    return path


def build(out, font_path):
    font = Font(font_path)
    os.makedirs(out, exist_ok=True)
    sv = lambda *p: os.path.join(out, "svg", *p)
    pn = lambda *p: os.path.join(out, "png", *p)
    for d in ("svg", "png/icon", "png/icon-square", "png/icon-circle", "png/mark",
              "png/wordmark", "png/wordmark-tile", "png/banner", "repo"):
        os.makedirs(os.path.join(out, d), exist_ok=True)

    svgs = {
        "aay-icon.svg": tile(font, MONOGRAM, shape="rounded", title="aay icon"),
        "aay-icon-square.svg": tile(font, MONOGRAM, shape="square", title="aay icon (square)"),
        "aay-icon-circle.svg": tile(font, MONOGRAM, shape="circle", title="aay icon (circle)"),
        "aay-mark-white.svg": transparent(font, MONOGRAM, COLORS["fg"], "aay mark"),
        "aay-mark-dark.svg": transparent(font, MONOGRAM, COLORS["ink_dark"], "aay mark"),
        "aay-wordmark-white.svg": transparent(font, WORDMARK, COLORS["fg"], "aay wordmark"),
        "aay-wordmark-dark.svg": transparent(font, WORDMARK, COLORS["ink_dark"], "aay wordmark"),
        "aay-wordmark-tile.svg": tile(font, WORDMARK, shape="rounded", title="aay wordmark tile"),
        "aay-banner.svg": banner(font, WORDMARK, title="aay banner"),
    }
    for name, doc in svgs.items():
        open(sv(name), "w", encoding="utf-8").write(doc)

    for n in (16, 24, 32, 48, 64, 96, 128, 180, 192, 256, 512, 1024):
        png(svgs["aay-icon.svg"], pn("icon", f"aay-icon-{n}.png"), n, n)
    for n in (120, 152, 167, 180, 192, 460, 512, 1024):
        png(svgs["aay-icon-square.svg"], pn("icon-square", f"aay-icon-square-{n}.png"), n, n)
    for n in (64, 128, 256, 512, 1024):
        png(svgs["aay-icon-circle.svg"], pn("icon-circle", f"aay-icon-circle-{n}.png"), n, n)
    for kind in ("mark", "wordmark"):
        for tone in ("white", "dark"):
            for h in (32, 64, 128, 256, 512):
                png(svgs[f"aay-{kind}-{tone}.svg"], pn(kind, f"aay-{kind}-{tone}-{h}h.png"), None, h)
    for n in (256, 512, 1024):
        png(svgs["aay-wordmark-tile.svg"], pn("wordmark-tile", f"aay-wordmark-tile-{n}.png"), n, n)
    png(svgs["aay-banner.svg"], pn("banner", "aay-banner-1280x640.png"), 1280, 640)
    png(svgs["aay-banner.svg"], pn("banner", "aay-banner-2560x1280.png"), 2560, 1280)

    # Files for the apt repo / website root
    repo = lambda n: os.path.join(out, "repo", n)
    png(svgs["aay-icon.svg"], repo("CydiaIcon.png"), 256, 256)
    png(svgs["aay-icon.svg"], repo("CydiaIcon@2x.png"), 120, 120)
    png(svgs["aay-icon.svg"], repo("CydiaIcon@3x.png"), 180, 180)
    png(svgs["aay-icon-square.svg"], repo("apple-touch-icon.png"), 180, 180)
    open(repo("favicon.svg"), "w", encoding="utf-8").write(svgs["aay-icon.svg"])
    ico = [Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svgs["aay-icon.svg"], width=n, height=n,
                                                             skip_system_fonts=True)))) for n in (48, 32, 16)]
    ico[0].save(repo("favicon.ico"), sizes=[(48, 48), (32, 32), (16, 16)], append_images=ico[1:])
    ico[0].save(os.path.join(out, "favicon.ico"), sizes=[(48, 48), (32, 32), (16, 16)], append_images=ico[1:])
    return svgs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    ap.add_argument("--font", default=os.environ.get("AAY_FONT", DEFAULT_FONT))
    a = ap.parse_args()
    if not os.path.isfile(a.font):
        sys.exit(f"Font not found: {a.font}\nGet Inter (OFL) from https://rsms.me/inter and pass --font .../Inter_28pt-Black.ttf")
    build(a.out, a.font)
    print("built", a.out)
