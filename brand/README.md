# aay brand kit

Two marks, both built from **Inter Display Black** with a GitHub-blue full stop:

| | Use it for |
|---|---|
| **Monogram `a.`** (`aay-icon*`, `aay-mark-*`) | Anything small or square: repo/app icons, avatars, favicons |
| **Wordmark `aay.`** (`aay-wordmark-*`, `aay-banner`) | Anything large and wide: site headers, README banners, social previews |

The wordmark becomes unreadable below roughly 64 px, so use the monogram there.

## Files

```
svg/                          editable vector masters (text is outlined: no font needed)
  aay-icon.svg                monogram on rounded tile (transparent corners)
  aay-icon-square.svg         monogram, full-bleed square (for platforms that apply their own mask)
  aay-icon-circle.svg         monogram on a circle
  aay-mark-white.svg          monogram only, transparent, for dark backgrounds
  aay-mark-dark.svg           monogram only, transparent, for light backgrounds
  aay-wordmark-white.svg      wordmark only, transparent, for dark backgrounds
  aay-wordmark-dark.svg       wordmark only, transparent, for light backgrounds
  aay-wordmark-tile.svg       wordmark on rounded tile
  aay-banner.svg              1280x640 social preview / README banner
png/
  icon/          aay-icon-{16,24,32,48,64,96,128,180,192,256,512,1024}.png
  icon-square/   aay-icon-square-{120,152,167,180,192,460,512,1024}.png   (GitHub avatar: 1024)
  icon-circle/   aay-icon-circle-{64,128,256,512,1024}.png
  mark/          aay-mark-{white,dark}-{32,64,128,256,512}h.png         (h = height in px)
  wordmark/      aay-wordmark-{white,dark}-{32,64,128,256,512}h.png
  wordmark-tile/ aay-wordmark-tile-{256,512,1024}.png
  banner/        aay-banner-1280x640.png, aay-banner-2560x1280.png
favicon.ico                   16 + 32 + 48 px
build_brand.py                regenerates everything above
```

Where they're used on dev.rtrdd.fyi: `CydiaIcon.png` (256), `CydiaIcon@2x.png` (120) and `CydiaIcon@3x.png` (180) are the rounded monogram tile; `apple-touch-icon.png` is the square tile (iOS masks it itself); `favicon.svg` / `favicon.ico` are the rounded tile.

## Colours

| Token | Hex | Notes |
|---|---|---|
| Background top | `#161B22` | vertical gradient, top |
| Background bottom | `#0D1117` | vertical gradient, bottom |
| Letters | `#FFFFFF` | `#0D1117` on light backgrounds |
| Accent (dot) | `#58A6FF` | |

## Construction

All values live at the top of `build_brand.py` (`MONOGRAM`, `WORDMARK`, `COLORS`, `RADIUS`).

- Typeface: Inter Display Black (`Inter_28pt-Black.ttf`, SIL Open Font License, https://rsms.me/inter)
- Letter spacing: -0.09 em; letters are measured by advance width
- Slant: 6° (letters only; the dot stays round and follows the slanted baseline)
- Dot: 0.42 × x-height (monogram) / 0.52 × x-height (wordmark), dipping 30% below the baseline
- Mark width: 58% (monogram) / 74% (wordmark) of the tile; x-height band centred at 45% of tile height
- Tile corner radius: 23.5% of tile size
- Optical centring: the mark is placed 60% of the way from its bounding-box centre to its centre of visual mass (`OPTICAL`), so it looks centred in tiles, circles and the banner

## Editing

- **Quick edit or recolour:** open any SVG in Figma, Illustrator, Inkscape or a text editor. Letters are one `<path id="letters">`, the full stop is `<circle id="dot">`, and the background gradient is `#bg`.
- **Change the design itself** (slant, spacing, size, colours): edit the values in `build_brand.py` and run:

```
pip install fonttools resvg-py pillow
python build_brand.py OUT_DIR --font path/to/Inter_28pt-Black.ttf
```

Every PNG and ICO is rendered from the SVGs, so the two always match.
