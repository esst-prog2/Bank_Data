"""Build compositions/plate.html from the promo page's own map plate.

The film's map is the page's real SVG (docs/index.html: land paths, 28 numbered markers,
Austria's amber disagreement ring), not a redrawing. Re-run after the page's map changes:

    python promo-video/tools/build_plate.py

Hand edits to compositions/plate.html are overwritten; change TEMPLATE below instead.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE.parent.parent / "docs" / "index.html"
OUT = HERE.parent / "compositions" / "plate.html"

page = PAGE.read_text(encoding="utf-8")
start = page.index('<svg class="map" id="map"')
svg = page[start:page.index("</svg>", start) + len("</svg>")]

# Keep land + desktop markers. Drop what the film doesn't use: the accessible title (the film
# has captions), the phone-only badges, the amber leader to the page's inset, the sea lettering.
svg = re.sub(r"<title[\s\S]*?</title>", "", svg, count=1)
svg = re.sub(r'<g class="badges"[\s\S]*?</g></g>(?=<g class="markers")', "", svg)
svg = re.sub(r'<path class="leader"[^>]*/>', "", svg)
svg = re.sub(r'<g class="seas"[\s\S]*?</g>', "", svg, count=1)
svg = svg.replace(
    '<svg class="map" id="map" viewBox="-160 90 800 415" role="img" aria-labelledby="map-title">',
    '<svg id="plate-svg" viewBox="-160 90 800 415" width="1920" height="996" aria-hidden="true">',
)
assert svg.count('class="mk') == 28, "expected the page's 28 markers"
assert 'class="badges"' not in svg and "leader" not in svg

TEMPLATE = Path(HERE / "plate.template.html").read_text(encoding="utf-8")
OUT.write_text(TEMPLATE.replace("<!--MAP-->", svg), encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB, 28 markers)")
