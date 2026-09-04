"""Render an original typographic black hole. Run from any directory.

No network, secrets, GPU, browser, or scheduled jobs are required.
Art-directed analytical fields evoke an accretion disk and gravitational
lensing; this is an illustration, not a numerical relativity simulation.
"""
from pathlib import Path
import json
import math
import random

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
W, H = CONFIG["width"], CONFIG["height"]
TAU = math.tau
FONT = ROOT / "fonts" / "RobotoMono.ttf"
ASSETS = ROOT / "assets"
ORIGIN = "Original procedural black-hole typography; outputs/scripts/render.py; art-directed analytical accretion and lens fields, not a physics simulation; font: Roboto Mono, SIL OFL 1.1."


def font(size):
    face = ImageFont.truetype(str(FONT), size)
    face.set_variation_by_name("Regular")
    return face


GLYPH = font(12)
PARTICLE = font(12)
NAME = font(58)
SMALL = font(20)
HANDLE = font(21)
RNG = random.Random(CONFIG["seed"])

CX, CY = 818, 237
TILT = -0.23
COS, SIN = math.cos(TILT), math.sin(TILT)
HORIZON = 68


def gaussian(value, center, width):
    return math.exp(-((value - center) / width) ** 2)


def project(u, v):
    return CX + u * COS - v * SIN, CY + u * SIN + v * COS


def ink(alpha, amber, theme):
    alpha = min(1, max(0, alpha))
    if theme == "light":
        pigment = (31 + 113 * amber, 35 + 51 * amber, 40 - 20 * amber)
        return tuple(round(255 - (255 - c) * alpha) for c in pigment)
    pigment = (208 + 16 * amber, 209 - 52 * amber, 204 - 143 * amber)
    return tuple(round(c * alpha) for c in pigment)


# Store the spatial field once. Motion is a continuous periodic advection
# of light through the field, with no random re-sampling between frames.
FIELD = []
for row, y in enumerate(range(57, 428, 9)):
    for col, x in enumerate(range(548, 1096, 7)):
        dx, dy = x + 3 - CX, y + 4 - CY
        u, v = dx * COS + dy * SIN, -dx * SIN + dy * COS
        radius = math.hypot(u, v)
        disk_r = math.hypot(u, v / 0.235)
        angle = math.atan2(v / 0.235, u)
        # The front of the disk passes over the lower part of the shadow.
        foreground = v > 13 and disk_r > 92
        in_shadow = radius < HORIZON
        disk = 0.0
        if 91 < disk_r < 261 and (not in_shadow or foreground):
            inner = 1 - math.exp(-(disk_r - 91) / 12)
            outer = max(0, 1 - (disk_r / 267) ** 4)
            disk = inner * outer * (0.5 + 0.5 * gaussian(disk_r, 140, 82))
        lens_r = math.hypot(u, v / 1.04)
        upper = (0.95 * gaussian(lens_r, 87, 7) + 0.30 * gaussian(lens_r, 102, 12)) if v < 2 else 0
        lower = 0.32 * gaussian(lens_r, 81, 6) if v > 0 else 0
        ring = 0.65 * gaussian(radius, HORIZON + 4, 3.2)
        lens = max(upper, lower, ring) if not in_shadow else 0
        if max(disk, lens) < 0.028:
            continue
        grain = 0.62 + 0.38 * RNG.random()
        # Dots and mathematical punctuation make the disk materially different
        # from the previous trefoil's braces; a few binary glyphs remain.
        glyph = RNG.choice("..::=+*0101")
        FIELD.append((x, y, u, v, disk_r, angle, disk, lens, grain, glyph))

DISTANT = [(RNG.uniform(549, 1090), RNG.uniform(40, 437), RNG.choice(".01"), RNG.random() * TAU) for _ in range(28)]
PACKETS = [(RNG.random(), RNG.uniform(0, TAU), RNG.choice("01.:")) for _ in range(26)]


def scene(t, theme="dark"):
    is_light = theme == "light"
    image = Image.new("RGB", (W, H), "#ffffff" if is_light else "#000000")
    draw = ImageDraw.Draw(image)
    for x, y, char, phase in DISTANT:
        if math.hypot(x - CX, y - CY) < 122:
            continue
        draw.text((x, y), char, font=GLYPH, fill=ink(0.07 + 0.025 * math.sin(TAU * t + phase), 0, theme))

    # The horizon is negative space in each palette, never a filled circle.
    # Its absence remains legible through the tightly bent surrounding field.
    for x, y, u, v, disk_r, angle, disk, lens, grain, glyph in FIELD:
        flow = 0.76 + 0.16 * math.sin(3 * angle - 0.045 * disk_r - 2 * TAU * t) + 0.08 * math.sin(5 * angle + 0.071 * disk_r + TAU * t)
        lensed_flow = 0.80 + 0.20 * math.sin(math.atan2(v, u) * 3 - TAU * t)
        # The approaching side is brighter, giving the disk a directional read.
        asymmetry = 0.72 + 0.28 * (1 - u / 270) / 2
        energy = min(1, max(disk * flow * asymmetry, lens * lensed_flow) * grain * 1.35) ** 0.62
        hot = max(0, math.cos(angle + TAU * t)) ** 10
        amber = min(1, 0.08 + 0.50 * lens + 0.70 * hot * disk)
        draw.text((x, y), glyph, font=GLYPH, fill=ink(energy, amber, theme))

    # Small packets orbit inward, fade, and reappear invisibly at the outer edge.
    # They brighten on the outer turn and disappear before the cycle seam.
    for offset, start, glyph in PACKETS:
        p = (t + offset) % 1
        a = start + 3.8 * p
        r = 269 - 161 * p
        u, v = r * math.cos(a), 0.235 * r * math.sin(a)
        if math.hypot(u, v) < HORIZON and v < 13:
            continue
        x, y = project(u, v)
        strength = 0.55 * math.sin(math.pi * p) ** 2
        if 549 < x < 1093 and 38 < y < 433:
            draw.text((x, y), glyph, font=PARTICLE, fill=ink(strength, 0.95, theme))

    x = 64
    for i, line in enumerate(CONFIG["name_lines"]):
        draw.text((x, 137 + 68 * i), line, font=NAME, fill="#1f2328" if is_light else "#e6e6e3")
    draw.text((x + 2, 296), CONFIG["handle"], font=HANDLE, fill="#905614" if is_light else "#c89550")
    draw.text((x + 2, 339), CONFIG["subtitle"], font=SMALL, fill="#59636e" if is_light else "#92958f")
    return image


def main():
    ASSETS.mkdir(exist_ok=True)
    sizes = {}
    for theme in ("dark", "light"):
        # One global palette per theme prevents quantization flicker.
        # Separate fixed palettes preserve white/black endpoints exactly.
        palette_data = []
        for i in range(128):
            palette_data += [round(i * 255 / 127) if theme == "light" else i * 2] * 3
        for i in range(128):
            if theme == "light":
                palette_data += [round(255 - (255 - c) * i / 127) for c in (144, 86, 20)]
            else:
                palette_data += [round(224 * i / 127), round(157 * i / 127), round(61 * i / 127)]
        palette = Image.new("P", (1, 1))
        palette.putpalette(palette_data)
        frames = []
        for i in range(CONFIG["frames"]):
            frame = scene(i / CONFIG["frames"], theme)
            frames.append(frame.quantize(palette=palette, dither=Image.Dither.NONE))
        stem = "field-light" if theme == "light" else "field"
        frames[0].save(ASSETS / f"{stem}.gif", save_all=True, append_images=frames[1:], duration=CONFIG["frame_duration_ms"], loop=0, optimize=True, disposal=1, comment=ORIGIN.encode())
        meta = PngImagePlugin.PngInfo()
        meta.add_text("Source", ORIGIN)
        meta.add_text("Theme", theme)
        scene(0, theme).save(ASSETS / f"{stem}-static.png", pnginfo=meta)
        sizes[theme] = (ASSETS / f"{stem}.gif").stat().st_size
        print(f"Rendered {theme}: {sizes[theme]} bytes", flush=True)
    report = {
        "dimensions": [W, H],
        "frames": CONFIG["frames"],
        "duration_seconds": CONFIG["frames"] * CONFIG["frame_duration_ms"] / 1000,
        "gif_bytes": sizes,
        "source": ORIGIN,
        "font_source": "https://github.com/google/fonts/tree/main/ofl/robotomono",
        "reference": "https://openai.com/pt-BR/index/previewing-gpt-5-6-sol/",
        "loop": "All motion uses integer-period sine/cosine waves; t=0 and t=1 are identical."
    }
    (ASSETS / "provenance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
