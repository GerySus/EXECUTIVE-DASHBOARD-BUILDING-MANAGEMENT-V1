"""One-off preprocessing: round coordinates, drop unused properties, and bake a
fixed fill/border color into each provinsi feature so the browser doesn't need
any extra per-feature computation.

Run once locally whenever data/indonesia_provinces.json changes:

    python3 pythonanywhere_app/tools/prepare_geojson.py
"""
import colorsys
import json
import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(APP_DIR)
SRC_PATH = os.path.join(ROOT_DIR, "data", "indonesia_provinces.json")
DST_PATH = os.path.join(APP_DIR, "static", "data", "indonesia_provinces.json")


def _round_coords(obj, nd=3):
    if isinstance(obj, list):
        if obj and isinstance(obj[0], (int, float)):
            return [round(x, nd) for x in obj]
        return [_round_coords(o, nd) for o in obj]
    return obj


def _hsl_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l / 100, s / 100)
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


def make_terrain_palette(n):
    palette = []
    for i in range(n):
        hue = 92 + (i * 9) % 40
        sat = 48 + (i * 11) % 24
        light = 40 + (i * 13) % 16
        fill = _hsl_hex(hue, sat, light)
        border = _hsl_hex(hue, sat, max(light - 14, 22))
        palette.append((fill, border))
    return palette


def main():
    with open(SRC_PATH, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    bucket_count = min(4, len(features) or 1)
    palette = make_terrain_palette(bucket_count)

    for i, feature in enumerate(features):
        feature["geometry"]["coordinates"] = _round_coords(feature["geometry"]["coordinates"])
        fill, border = palette[i % bucket_count]
        feature["properties"] = {"fill": fill, "border": border}

    os.makedirs(os.path.dirname(DST_PATH), exist_ok=True)
    with open(DST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))

    print(f"wrote {DST_PATH} ({os.path.getsize(DST_PATH):,} bytes, {len(features)} features)")


if __name__ == "__main__":
    main()
