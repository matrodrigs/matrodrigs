"""Original ASCII accretion field, rendered offline into theme-aware GIFs.

Every mark in the black-hole field is a printable ASCII glyph. Analytical fields describe
an artistic interpretation of accretion and lensing, not a relativity solver.
Motion is periodic, deterministic, and independent of the output frame rate.
"""
from pathlib import Path
import argparse
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
ASSETS = ROOT / "assets"
FONT = ROOT / "fonts" / "RobotoMono.ttf"
W, H = CONFIG["width"], CONFIG["height"]
TAU = math.tau
CELL_W, CELL_H = 7, 9
COLS, ROWS = W // CELL_W, H // CELL_H
CX, CY, HORIZON = 754, 234, 68
SCALE = 1.38
TILT = -0.23
COS, SIN = math.cos(TILT), math.sin(TILT)
ORIGIN = (
    "Original procedural ASCII animation; scripts/render.py; art-directed "
    "accretion, photon rings and orbiting glyphs. Not a scientific simulation. "
    "Roboto Mono, SIL OFL 1.1. User-supplied black-hole image is a composition "
    "reference only; no reference-image pixels are used."
)
THEMES = {
    "dark": {
        "background": (0, 0, 0), "warm": (224, 157, 61),
        "cool": (208, 209, 204), "hot": (230, 230, 227),
        "text": (230, 230, 227), "muted": (146, 149, 143),
    },
    "light": {
        "background": (255, 255, 255), "warm": (144, 86, 20),
        "cool": (31, 35, 40), "hot": (31, 35, 40),
        "text": (31, 35, 40), "muted": (89, 99, 110),
    },
}


def font(size):
    face = ImageFont.truetype(str(FONT), size)
    face.set_variation_by_name("Regular")
    return face


GLYPH, NAME, HANDLE, SMALL = font(12), font(58), font(21), font(20)
CHARS = " .:=+*01"
# Fixed glyph tiles keep the characters sharp and avoid a million font calls.
ATLAS = []
for char in CHARS:
    tile = Image.new("L", (CELL_W, CELL_H))
    ImageDraw.Draw(tile).text((0, -3), char, font=GLYPH, fill=255)
    ATLAS.append(np.asarray(tile, dtype=np.float32) / 255)
ATLAS = np.asarray(ATLAS)
Y, X = np.mgrid[:ROWS, :COLS]
DX, DY = X * CELL_W + CELL_W / 2 - CX, Y * CELL_H + CELL_H / 2 - CY
U, V = (DX * COS + DY * SIN) / SCALE, (-DX * SIN + DY * COS) / SCALE
R, ANGLE = np.hypot(U, V), np.arctan2(V, U)
DISK_R, DISK_A = np.hypot(U, V / 0.235), np.arctan2(V / 0.235, U)
RNG = np.random.default_rng(CONFIG["seed"])
GRAIN, PHASE, HASH = RNG.uniform(0.62, 1.0, R.shape), RNG.uniform(0, TAU, R.shape), RNG.uniform(0, 1, R.shape)
BASE_GLYPHS = RNG.choice([1, 1, 2, 2, 3, 4, 5, 6, 7, 6, 7], size=R.shape)
# A seeded polar texture is transported around the orbit. Unlike frame-wise
# random resampling, the same glyph patterns follow coherent circular paths.
ORBIT_GLYPHS = RNG.choice([1, 1, 2, 2, 3, 4, 5, 6, 7, 6, 7], size=(96, 512))
ORBIT_GRAIN = RNG.uniform(0.62, 1.0, size=(96, 512))


def gauss(value, center, width):
    return np.exp(-((value - center) / width) ** 2)


def smoothstep(start, end, value):
    p = np.clip((value - start) / (end - start), 0, 1)
    return p * p * (3 - 2 * p)


def orbit_texture(radius, angle, t):
    """Periodic polar advection with glyph spacing tied to each annulus."""
    row = np.clip(np.floor(radius / 5.2).astype(int), 0, 95)
    sectors = np.clip(np.rint(TAU * (row + 0.5) * 5.2 * SCALE / 8).astype(int), 48, 512)
    position = ((angle / TAU + t) % 1) * sectors
    column = np.floor(position).astype(int)
    fraction = position - column
    following = (column + 1) % sectors
    grain = ORBIT_GRAIN[row, column] * (1 - fraction) + ORBIT_GRAIN[row, following] * fraction
    return ORBIT_GLYPHS[row, column], grain


def field(t):
    """The incumbent black/gray/amber field, enlarged without changing its grammar.

    Three curved streams feed light inward. Their characters live on the same
    lattice as the disk, avoiding the detached, overlapping sprite band from v1.
    """
    clock = TAU * t
    radial = (1 - np.exp(-np.maximum(DISK_R - 91, 0) / 12))
    radial *= np.maximum(0, 1 - (DISK_R / 267) ** 4)
    disk = radial * (0.5 + 0.5 * gauss(DISK_R, 140, 82))
    foreground = (V > 13) & (DISK_R > 92)
    disk *= (DISK_R < 261) & ((R >= HORIZON) | foreground)
    lens_r = np.hypot(U, V / 1.04)
    upper = (0.95 * gauss(lens_r, 87, 7) + 0.30 * gauss(lens_r, 102, 12)) * (V < 2)
    lower = 0.32 * gauss(lens_r, 81, 6) * (V > 0)
    ring = 0.65 * gauss(R, HORIZON + 4, 3.2)
    lens = np.maximum.reduce([upper, lower, ring]) * (R >= HORIZON)
    flow = 0.78 + 0.14 * np.sin(3 * DISK_A - 0.045 * DISK_R + 2 * clock)
    flow += 0.06 * np.sin(5 * DISK_A + 0.071 * DISK_R + 3 * clock)
    lensed_flow = 0.84 + 0.16 * np.sin(2 * ANGLE + clock)
    disk_codes, disk_grain = orbit_texture(DISK_R, DISK_A, t)
    # Keep the original texture mostly stationary. Three narrow annuli carry
    # gentle motion; the shadow and photon-ring characters do not churn.
    annulus = np.floor(DISK_R / 5.2).astype(int)
    transport = (annulus % 9 == 3) & (DISK_R > 120) & (disk > 1.4 * lens)
    body_codes = np.where(transport, disk_codes, BASE_GLYPHS)
    grain = np.where(transport, 0.80 * GRAIN + 0.20 * disk_grain, GRAIN)
    asymmetry = 0.72 + 0.28 * (1 - U / 270) / 2
    energy = np.clip(np.maximum(disk * flow * asymmetry, lens * lensed_flow) * grain * 1.65, 0, 1) ** 0.62
    energy *= np.maximum(disk, lens) > 0.028
    hot = np.maximum(0, np.cos(DISK_A + clock)) ** 10
    amber = np.clip(0.08 + 0.50 * lens + 0.70 * hot * disk, 0, 1)

    # Fixed logarithmic paths; traveling pulses advance toward smaller radii.
    bend = ANGLE + 1.5 * np.log(np.maximum(R, 80) / 110)
    lane = (0.5 + 0.5 * np.cos(3 * bend + 0.45)) ** 46
    envelope = smoothstep(90, 116, R) * (1 - smoothstep(183, 241, R))
    incoming = (0.5 + 0.5 * np.sin(R * 0.087 + 3 * clock)) ** 3
    streams = lane * envelope * (0.07 + 0.34 * incoming)
    streams *= 1 - smoothstep(0.12, 0.48, energy)
    body_visible = energy >= np.maximum(streams, 0.022)
    amber = np.where(streams > energy, 0.13 + 0.42 * incoming, amber)
    energy = np.maximum(energy, streams)
    energy *= smoothstep(397, 454, X * CELL_W)
    energy *= 1 - smoothstep(W - 30, W - 8, X * CELL_W)
    energy *= smoothstep(13, 37, Y * CELL_H) * (1 - smoothstep(H - 34, H - 10, Y * CELL_H))
    stars = (HASH > 0.996) * (R > 131) * (X * CELL_W > 446)
    energy = np.maximum(energy, stars * (0.06 + 0.02 * np.sin(PHASE + clock)))
    indices = np.where(energy > 0.022, np.where(body_visible, body_codes, BASE_GLYPHS), 0)
    return np.clip(energy, 0, 1), amber, indices


def blend(theme, strength, accent="warm"):
    colors = THEMES[theme]
    return tuple(round(a + (b - a) * max(0, min(1, strength)))
                 for a, b in zip(colors["background"], colors[accent]))


def draw_identity(draw, theme):
    colors = THEMES[theme]
    for line_index, line in enumerate(CONFIG["name_lines"]):
        draw.text((64, 137 + 68 * line_index), line, font=NAME, fill=colors["text"])
    draw.text((66, 296), CONFIG["handle"], font=HANDLE,
              fill=(144, 86, 20) if theme == "light" else (200, 149, 80))
    draw.text((66, 339), CONFIG["subtitle"], font=SMALL, fill=colors["muted"])


def draw_infall(draw, t, theme):
    """Readable echoes feed into the near-side disk, without moving the name."""
    for index, char in enumerate("Rodrigues01{}"):
        p = (t + index / 13) % 1
        q = 1 - p
        # Cubic path from the final name letters to the front of the orbit.
        x = q**3 * 380 + 3*q*q*p * 434 + 3*q*p*p * 492 + p**3 * 657
        y = q**3 * 251 + 3*q*q*p * 260 + 3*q*p*p * 343 + p**3 * 307
        strength = 0.49 * math.sin(math.pi * p) ** 2
        draw.text((x, y), char, font=GLYPH,
                  fill=blend(theme, strength, "warm" if p > 0.70 else "cool"))


def scene(t, theme="dark"):
    energy, amber, indices = field(t % 1)
    colors = THEMES[theme]
    bg = np.asarray(colors["background"], dtype=np.float32)
    if theme == "light":
        pigment = np.stack((31 + 113 * amber, 35 + 51 * amber, 40 - 20 * amber), axis=-1)
    else:
        pigment = np.stack((208 + 16 * amber, 209 - 52 * amber, 204 - 143 * amber), axis=-1)
    masks = ATLAS[indices]
    pixels = bg + (pigment - bg)[:, :, None, None, :] * masks[..., None] * energy[:, :, None, None, None]
    pixels = pixels.transpose(0, 2, 1, 3, 4).reshape(ROWS * CELL_H, COLS * CELL_W, 3)
    image = Image.new("RGB", (W, H), tuple(colors["background"]))
    image.paste(Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8)), (0, 0))
    draw = ImageDraw.Draw(image)
    draw_infall(draw, t % 1, theme)
    draw_identity(draw, theme)
    return image


def palette(theme):
    """Shared per-theme palette prevents frame-to-frame color flicker."""
    data = []
    for step in range(128):
        data.extend([round(step * 255 / 127)] * 3)
    for step in range(128):
        data.extend(blend(theme, step / 127, "warm"))
    result = Image.new("P", (1, 1))
    result.putpalette(data)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stills", action="store_true", help="Only render static previews")
    args = parser.parse_args()
    ASSETS.mkdir(exist_ok=True)
    sizes = {}
    for theme in THEMES:
        stem = "field-light" if theme == "light" else "field"
        fixed_palette = palette(theme)
        meta = PngImagePlugin.PngInfo()
        meta.add_text("Source", ORIGIN)
        meta.add_text("Theme", theme)
        scene(0, theme).save(ASSETS / f"{stem}-static.png", pnginfo=meta)
        if args.stills:
            continue
        frames = []
        for index in range(CONFIG["frames"]):
            frame = scene(index / CONFIG["frames"], theme)
            frames.append(frame.quantize(palette=fixed_palette, dither=Image.Dither.NONE))
            if index % 40 == 0:
                print(f"{theme}: {index}/{CONFIG['frames']}", flush=True)
        frames[0].save(ASSETS / f"{stem}.gif", save_all=True, append_images=frames[1:],
                       duration=CONFIG["frame_duration_ms"], loop=0, optimize=True,
                       disposal=1, comment=ORIGIN.encode())
        sizes[theme] = (ASSETS / f"{stem}.gif").stat().st_size
        print(f"Rendered {theme}: {sizes[theme]:,} bytes", flush=True)
    if not args.stills:
        report = {
            "dimensions": [W, H], "frames": CONFIG["frames"],
            "duration_seconds": CONFIG["frames"] * CONFIG["frame_duration_ms"] / 1000,
            "gif_bytes": sizes, "source": ORIGIN,
            "font_source": "https://github.com/google/fonts/tree/main/ofl/robotomono",
            "reference": "User-provided black-hole composition; reference pixels not used.",
            "loop": "Three narrow seeded glyph currents orbit once per loop; gentle integer-period light waves, inward pulses and endpoint-faded letter echoes preserve the seam.",
            "motion": "Most glyphs stay fixed. Three narrow disk currents orbit in 16 seconds; light drifts softly around stationary photon-ring characters. Composition, silhouette and identity stay fixed.",
            "scale_relative_to_original": SCALE,
            "ascii": "All marks in the black-hole field are printable ASCII characters.",
        }
        (ASSETS / "provenance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
