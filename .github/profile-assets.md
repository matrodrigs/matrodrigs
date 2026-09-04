# Profile artwork

The README selects the dark or light GIF through pure `prefers-color-scheme` sources. Do not combine theme and reduced-motion conditions in those sources: GitHub's `themed-picture` component replaces the entire media query in fixed themes and would select a static PNG before the GIF, even when reduced motion is off.

Static alternatives remain available: [dark](../assets/field-static.png) and [light](../assets/field-light-static.png). The local preview supports pausing and the system's reduced-motion preference; the published README uses GIFs for both themes.

To regenerate the original typographic black hole, use Python 3.10 or newer from the repository root:

```sh
python -m pip install -r requirements.txt
python scripts/render.py
```

Edit `profile.json` for the name, subtitle, or animation timing. The renderer writes the two GIFs, static PNGs, and provenance record into `assets/`. Font licensing is in `fonts/OFL.txt`.

The artwork is an artistic interpretation of an accretion disk and bent light, not a scientific simulation. No API key, external widget, or scheduled regeneration is required.
