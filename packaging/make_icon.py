"""Build packaging/lingogeek.ico from the app icon."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main() -> int:
    src = ROOT / "icons" / "lingogeek.png"
    if not src.exists():
        print("No source icon found; skipping icon build.")
        return 0
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not available; skipping icon build.")
        return 0
    out = ROOT / "packaging" / "lingogeek.ico"
    Image.open(src).convert("RGBA").save(out, format="ICO", sizes=SIZES)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
