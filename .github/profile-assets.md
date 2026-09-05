# Profile artwork

The README selects the dark or light GIF through pure `prefers-color-scheme` sources. Do not combine theme and reduced-motion conditions in those sources: GitHub's `themed-picture` component replaces the entire media query in fixed themes and would select a static PNG before the GIF, even when reduced motion is off.

Static alternatives remain available: [dark](../assets/field-static.png) and [light](../assets/field-light-static.png). The README uses GIFs for both themes; those embedded GIFs do not provide their own pause controls.

The banner restores the incumbent ASCII design: a tilted disk of gray code, amber arcs of bent light, and a silent center. The black-hole geometry is 38% larger than the original. Three curved character streams carry light inward, and faint letter echoes travel from the name into the near-side disk. The name, handle, and education remain stationary and retain their original typography. Identity is also present as native README text for mobile readers, text selection, and assistive technology.

The dark palette restores pure black, neutral gray, and restrained amber from the original profile artwork. The light variant restores white, graphite, and ochre. Both themes use fixed neutral and amber GIF palette ramps to avoid quantization flicker. The 1120 × 480 banner has 320 frames at 20 fps and loops every 16 seconds.

Most of the original glyph texture remains stationary. Three narrow currents carry seeded glyph patterns slowly around the disk, completing one orbit per loop. The photon-ring characters stay fixed while soft light and amber highlights drift around them. The silhouette, original typography, and incoming trails retain their composition. No random texture is regenerated between frames.

To regenerate the original typographic black hole, use Python 3.11 or newer from the repository root:

```sh
python -m pip install -r requirements.txt
python scripts/render.py
```

Edit `profile.json` for the name, subtitle, or animation timing. The renderer writes the two GIFs, static PNGs, and provenance record into `assets/`. Font licensing is in `fonts/OFL.txt`.

Use `python scripts/render.py --stills` to render only the PNG previews. All drawing is local and deterministic. The user-provided image influenced composition only: the renderer does not load or transform any reference-image pixels.

The artwork is an artistic interpretation of an accretion disk and bent light, not a scientific simulation. No API key, external widget, or scheduled regeneration is required.
