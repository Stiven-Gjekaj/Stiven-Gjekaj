"""Build the tech stack icon rows in assets/stack/.

Each row is one SVG in the style of skillicons.dev: 256px rounded tiles,
shown at 48px, 300 units apart. Icons skillicons does not have are drawn
here in the same style.

Usage, from the repository root:

    python3 scripts/build_stack.py

Edit ROWS below to change the stack, then commit the files in assets/stack/.
Only the Python standard library is needed. It downloads icons from
skillicons.dev and cdn.simpleicons.org, and reads the vendored logos in
assets/icons/src/.
"""
import base64
import http.client
import re
import struct
import time
import urllib.request
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "stack"
SRC = Path(__file__).resolve().parent.parent / "assets" / "icons" / "src"  # vendored logos

# Each row: file name -> icons, left to right. Names are skillicons ids,
# or one of the custom tiles defined further down.
ROWS = {
    "languages": ["rust", "python", "c", "objc", "swift", "ts", "js", "css", "kotlin", "java", "go"],
    "apps": ["react", "vue", "wasm", "slint", "swiftui", "compose", "fastapi", "streamlit", "plotly"],
    "media": ["opengles", "sdl", "ffmpeg", "vlc", "whisper"],
    "data": ["sqlite", "postgres", "prometheus", "docker", "gradle", "xcode", "theos", "llvm", "githubactions"],
    "platforms": ["windows", "apple", "linux", "android", "minecraft", "fabric"],
}

DARK = "#242938"  # the dark tile colour skillicons uses


def fetch(url):
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "build_stack"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode()
        except (OSError, http.client.HTTPException):
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))


def skillicon(name):
    """The inner 256x256 <svg> of one skillicons icon."""
    src = fetch(f"https://skillicons.dev/icons?i={name}")
    start = src.index("<svg", src.index("<g "))
    return src[start:src.rindex("</g>")].strip()


def simple_icon_path(name):
    """The path data of a Simple Icons glyph (a 24x24 box)."""
    return re.search(r' d="([^"]+)"', fetch(f"https://cdn.simpleicons.org/{name}")).group(1)


def tile(fill, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" fill="none" '
            f'viewBox="0 0 256 256"><rect width="256" height="256" rx="60" fill="{fill}"/>{body}</svg>')


def glyph_tile(name, fill, scale=7.0, dy=0.0, extra=""):
    off = (256 - 24 * scale) / 2
    return tile(fill, f'<path fill="#fff" transform="translate({off} {off + dy}) scale({scale})" '
                      f'd="{simple_icon_path(name)}"/>{extra}')


def objc():
    # No official mark: its [object message] brackets around skillicons' own C glyph.
    c = re.search(r'<path d="([^"]+)" fill="white"', skillicon("c")).group(1)
    return tile(DARK,
                f'<path fill="#fff" transform="translate(128 128) scale(0.56) translate(-128 -128)" d="{c}"/>'
                '<path d="M84 58H48V198H84M172 58H208V198H172" stroke="#438EFF" stroke-width="22" '
                'stroke-linecap="round" stroke-linejoin="round" fill="none"/>')


# "ES" in Liberation Sans Bold, already turned into an outline.
ES = ("M72.791 219.647V156.353H122.564V166.595H86.043V182.497H119.824V192.739H86.043V209.405H124.406"
      "V219.647ZM185.770 201.409Q185.770 210.708 178.874 215.627Q171.979 220.546 158.637 220.546"
      "Q146.463 220.546 139.545 216.233Q132.627 211.921 130.650 203.161L143.453 201.050"
      "Q144.756 206.081 148.529 208.350Q152.303 210.618 158.996 210.618Q172.877 210.618 172.877 202.173"
      "Q172.877 199.478 171.282 197.726Q169.688 195.974 166.790 194.806Q163.893 193.638 155.672 191.976"
      "Q148.574 190.313 145.789 189.303Q143.004 188.292 140.758 186.922Q138.512 185.552 136.939 183.620"
      "Q135.367 181.688 134.491 179.083Q133.615 176.478 133.615 173.108Q133.615 164.528 140.062 159.969"
      "Q146.508 155.409 158.816 155.409Q170.586 155.409 176.493 159.093Q182.400 162.776 184.107 171.267"
      "L171.260 173.019Q170.271 168.931 167.239 166.864Q164.207 164.798 158.547 164.798"
      "Q146.508 164.798 146.508 172.345Q146.508 174.815 147.788 176.388Q149.068 177.960 151.584 179.061"
      "Q154.100 180.161 161.781 181.823Q170.900 183.755 174.831 185.395Q178.762 187.034 181.053 189.213"
      "Q183.344 191.392 184.557 194.424Q185.770 197.456 185.770 201.409Z")


def whisper():
    # An original waveform; OpenAI's mark is not used.
    bars = [36, 70, 112, 150, 104, 132, 82, 120, 58, 30]
    bw, gap = 12, 6
    x0 = 128 - (len(bars) * bw + (len(bars) - 1) * gap) / 2
    return tile(DARK, "".join(
        f'<rect x="{x0 + i * (bw + gap):.1f}" y="{128 - h / 2:.1f}" width="{bw}" height="{h}" '
        f'rx="{bw / 2}" fill="#fff"/>' for i, h in enumerate(bars)))


def png_pixels(path):
    """Width, height, and RGBA rows of a small PNG (palette or RGBA, no interlace)."""
    data = path.read_bytes()
    pos, idat, plte, trns = 8, b"", b"", b""
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        pos += n + 12
        if kind == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
        elif kind == b"PLTE":
            plte = body
        elif kind == b"tRNS":
            trns = body
        elif kind == b"IDAT":
            idat += body
    raw = zlib.decompress(idat)
    bpp = {3: depth / 8, 6: 4}[ctype]
    stride = int(-(-w * bpp // 1))
    step = max(1, int(bpp))
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f, line = raw[i], bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - step] if x >= step else 0
            b, c = prev[x], prev[x - step] if x >= step else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if ctype == 6:
            rows.append([tuple(line[x * 4:x * 4 + 4]) for x in range(w)])
        else:
            per = 8 // depth
            idx = [(line[x // per] >> (8 - depth * (x % per + 1))) & ((1 << depth) - 1) for x in range(w)]
            rows.append([(*plte[k * 3:k * 3 + 3], trns[k] if k < len(trns) else 255) for k in idx])
    return w, h, rows


def pixel_art(path, size):
    """A pixel-art PNG as crisp SVG rects, centred in the tile and `size` units tall."""
    w, h, rows = png_pixels(path)
    px = size / h
    x0, y0 = (256 - w * px) / 2, (256 - h * px) / 2
    out = []
    for y, line in enumerate(rows):
        x = 0
        while x < w:
            r, g, b, a = line[x]
            run = 1
            while x + run < w and line[x + run] == line[x]:
                run += 1
            if a:
                op = "" if a == 255 else f' fill-opacity="{a / 255:.2f}"'
                out.append(f'<rect x="{x0 + x * px:.2f}" y="{y0 + y * px:.2f}" width="{run * px + 0.05:.2f}" '
                           f'height="{px + 0.05:.2f}" fill="#{r:02X}{g:02X}{b:02X}"{op}/>')
            x += run
    return "".join(out)


def embedded(path, kind, x, y, size, clip=None):
    """A raster image from SRC, embedded as base64."""
    data = base64.b64encode((SRC / path).read_bytes()).decode()
    cp = f' clip-path="url(#{clip})"' if clip else ""
    return (f'<image x="{x}" y="{y}" width="{size}" height="{size}"{cp} '
            f'href="data:image/{kind};base64,{data}" xlink:href="data:image/{kind};base64,{data}"/>')


def minecraft():
    # Minecraft's own grass block render (from minecraft.wiki) on the dark tile.
    return tile(DARK, embedded("minecraft-grass-block.png", "png", 40, 40, 176))


def fabric():
    # Fabric's own logo (from fabricmc.net), pixel for pixel, on the dark tile.
    return tile(DARK, pixel_art(SRC / "fabric-logo.png", 180))


def android():
    # The Android robot head from Simple Icons, in Android green, on the dark tile.
    return glyph_tile("android", DARK, scale=7.5).replace('fill="#fff"', 'fill="#3DDC84"')


def photo_tile(name):
    """A whole 256x256 tile from the JPEG SRC/<name>-tile.jpg, clipped to the tile shape."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="256" '
            f'height="256" viewBox="0 0 256 256"><defs><clipPath id="{name}-tile">'
            '<rect width="256" height="256" rx="60"/></clipPath></defs>'
            f'{embedded(f"{name}-tile.jpg", "jpeg", 0, 0, 256, clip=f"{name}-tile")}</svg>')


def swiftui():
    # Apple's own SwiftUI icon (from developer.apple.com).
    return photo_tile("swiftui")


def vlc():
    # VLC's own cone (from the VideoLAN source tree) on the dark tile.
    paths = re.findall(r'<path [^>]+/>', (SRC / "vlc-cone.svg").read_text())
    return tile(DARK, f'<g transform="translate(128 128) scale(1.5) translate(-65 -65)">{"".join(paths)}</g>')


def xcode():
    # Apple's own Xcode icon (from developer.apple.com), already placed on the dark tile.
    return photo_tile("xcode")


def sdl():
    # SDL's own logo (from the SDL source tree), on white because its letters are dark navy.
    return photo_tile("sdl")


def svg_logo(name, fill=DARK, size=196, skip=0):
    """A vendored SVG logo from SRC, centred on a tile. `skip` drops that many
    leading elements, such as a logo's own background square."""
    src = (SRC / f"{name}.svg").read_text()
    box = re.search(r'viewBox="([^"]+)"', src).group(1)
    inner = src[src.index(">") + 1:src.rindex("</svg>")]
    for _ in range(skip):
        inner = inner[re.search(r"/>|</path>", inner).end():]
    off = (256 - size) / 2
    return tile(fill, f'<svg x="{off}" y="{off}" width="{size}" height="{size}" viewBox="{box}">{inner}</svg>')


def theos():
    # Theos's own mark (from theos.dev), without its square, on the dark tile.
    return svg_logo("theos", size=236, skip=1)


def streamlit():
    # Streamlit's own mark (from the Streamlit source tree) on the dark tile.
    return svg_logo("streamlit", size=200)


def llvm():
    # LLVM's own wyvern (from llvm.org), already placed on the dark tile.
    return photo_tile("llvm")


def compose():
    # The Jetpack Compose logo (from developer.android.com) on the dark tile. Its ids
    # get a prefix so they cannot clash with other icons in the same row.
    src = (SRC / "compose-logo.svg").read_text()
    src = re.sub(r'id="(\w)"', r'id="compose-\1"', src)
    src = re.sub(r'url\(#(\w)\)', r'url(#compose-\1)', src)
    inner = src[src.index(">") + 1:src.rindex("</svg>")]
    return tile(DARK, f'<svg x="12" y="12" width="232" height="232" viewBox="40 40 400 400">{inner}</svg>')


CUSTOM = {
    "minecraft": minecraft,
    "fabric": fabric,
    "android": android,
    "swiftui": swiftui,
    "compose": compose,
    "vlc": vlc,
    "xcode": xcode,
    "sdl": sdl,
    "theos": theos,
    "streamlit": streamlit,
    "plotly": lambda: glyph_tile("plotly", DARK).replace('fill="#fff"', 'fill="#7A76FF"'),
    "llvm": llvm,
    "objc": objc,
    "slint": lambda: glyph_tile("slint", "#2379F4"),
    "ffmpeg": lambda: glyph_tile("ffmpeg", "#007808"),
    "opengles": lambda: glyph_tile("opengl", "#5586A4", scale=9.6, dy=-46,
                                   extra=f'<path fill="#fff" d="{ES}"/>'),
    "whisper": whisper,
}


def youtube():
    # The red play button on the dark tile, like skillicons' Gmail. Simple Icons
    # cuts the triangle out, so a white triangle sits underneath to fill it.
    scale, off = 7.5, (256 - 24 * 7.5) / 2
    t = f'transform="translate({off} {off}) scale({scale})"'
    return tile(DARK, f'<path fill="#fff" {t} d="M9.545 15.568V8.432L15.818 12z"/>'
                      f'<path fill="#FF0000" {t} d="{simple_icon_path("youtube")}"/>')


NUM = r"-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?"
ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def last_subpath(d):
    """The last subpath of `d`, rewritten to start from an absolute point."""
    toks = re.findall(r"[A-Za-z]|" + NUM, d)
    x = y = sx = sy = 0.0
    i, cmd, start = 0, None, (0.0, 0.0)
    while i < len(toks):
        if toks[i].isalpha():
            cmd, i = toks[i], i + 1
        if cmd in "Zz":
            x, y = sx, sy
            continue
        k = ARGS[cmd.upper()]
        a = [float(v) for v in toks[i:i + k]]
        i += k
        rel, c = cmd.islower(), cmd.upper()
        if c == "M":
            x, y = (x + a[0], y + a[1]) if rel else (a[0], a[1])
            sx, sy, start = x, y, (x, y)
            cmd = "l" if rel else "L"
        elif c == "H":
            x = x + a[0] if rel else a[0]
        elif c == "V":
            y = y + a[0] if rel else a[0]
        else:
            x, y = (x + a[-2], y + a[-1]) if rel else (a[-2], a[-1])
    tail = re.split(r"(?=[Mm])", d)[-1]
    m = re.match(r"[Mm]\s*" + NUM + r"\s*,?\s*" + NUM, tail)
    return f"M{start[0]:.3f} {start[1]:.3f}" + tail[m.end():]


def kofi():
    # A white cup with a red heart, as in Ko-fi's own logo. The heart is the
    # last subpath of the Simple Icons glyph, drawn again on top in red.
    d = simple_icon_path("kofi")
    t = f'transform="translate({(256 - 24 * 7.5) / 2} {(256 - 24 * 7.5) / 2}) scale(7.5)"'
    return tile(DARK, f'<path fill="#fff" {t} d="{d}"/><path fill="#FF5E5B" {t} d="{last_subpath(d)}"/>')


def cydia():
    # Cydia's own logo (from Wikipedia), embedded and clipped to the tile shape.
    png = base64.b64encode((SRC / "cydia-logo.png").read_bytes()).decode()
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="256" height="256" viewBox="0 0 256 256"><defs><clipPath id="cydia-tile">'
            '<rect width="256" height="256" rx="60"/></clipPath></defs>'
            f'<image width="256" height="256" clip-path="url(#cydia-tile)" '
            f'href="data:image/png;base64,{png}" xlink:href="data:image/png;base64,{png}"/></svg>')


def sidestore():
    # SideStore's own glyph (from sidestore.io) on its cyan-to-magenta gradient.
    paths = "".join(f'<path d="{d}"/>' for d in
                    re.findall(r' d="([^"]+)"', (SRC / "sidestore-glyph.svg").read_text()))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
            '<defs><linearGradient id="ss-bg" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0" stop-color="#07DAF9"/><stop offset="0.5" stop-color="#6A6CF6"/>'
            '<stop offset="1" stop-color="#DC05F9"/></linearGradient>'
            '<linearGradient id="ss-shade" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#000" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#000" stop-opacity="0.12"/></linearGradient></defs>'
            '<rect width="256" height="256" rx="60" fill="url(#ss-bg)"/>'
            '<rect width="256" height="256" rx="60" fill="url(#ss-shade)"/>'
            f'<g fill="#fff" transform="translate(53 53) scale(0.75)">{paths}</g></svg>')


# Single icons for the header, written to assets/icons/.
HEADER = {"kofi": kofi, "cydia": cydia, "sidestore": sidestore}  # youtube() is kept above if you want it back


def row(names):
    vw = len(names) * 300 - 44
    parts = "".join(
        f'<g transform="translate({i * 300}, 0)">{CUSTOM[n]() if n in CUSTOM else skillicon(n)}</g>'
        for i, n in enumerate(names))
    return (f'<svg width="{vw * 48 / 256:g}" height="48" viewBox="0 0 {vw} 256" fill="none" '
            'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'version="1.1">{parts}</svg>')


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for key, names in ROWS.items():
        (OUT / f"{key}.svg").write_text(row(names))
        print(f"assets/stack/{key}.svg: {', '.join(names)}")
    icons = OUT.parent / "icons"
    icons.mkdir(parents=True, exist_ok=True)
    for key, make in HEADER.items():
        (icons / f"{key}.svg").write_text(
            '<svg width="48" height="48" viewBox="0 0 256 256" fill="none" '
            f'xmlns="http://www.w3.org/2000/svg">{make()}</svg>')
        print(f"assets/icons/{key}.svg")
