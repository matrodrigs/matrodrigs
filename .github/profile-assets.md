# Profile artwork

The README selects the dark or light GIF through `picture` sources and provides matching static PNGs for reduced-motion preferences.

To regenerate the original typographic black hole, use Python 3.10 or newer from the repository root:

```sh
python -m pip install -r requirements.txt
python scripts/render.py
```

Edit `profile.json` for the name, subtitle, or animation timing. The renderer writes the two GIFs, static PNGs, and provenance record into `assets/`. Font licensing is in `fonts/OFL.txt`.

The artwork is an artistic interpretation of an accretion disk and bent light, not a scientific simulation. No API key, external widget, or scheduled regeneration is required.
