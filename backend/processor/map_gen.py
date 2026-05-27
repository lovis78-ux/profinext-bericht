"""
Generate a project location map page using OpenStreetMap tiles.
"""
import io
import requests
import fitz
from PIL import Image, ImageDraw
from processor.ci_helpers import (
    draw_header, draw_footer, draw_section_title,
    MARGIN_L, MARGIN_R, HEADER_H, FOOTER_Y, CONTENT_TOP,
    PAGE_W, PAGE_H, DARK_TEXT, TEAL,
)
from processor.extractor import ProjectData

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "ProjektberichtOptimizer/1.0"


def geocode_address(address: str) -> tuple[float, float] | None:
    """Returns (lat, lon) or None."""
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": address + ", Deutschland", "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None


def generate_map_image(lat: float, lon: float, zoom: int = 12) -> bytes | None:
    """Generate a static OSM map image as PNG bytes."""
    try:
        from staticmap import StaticMap, CircleMarker
        m = StaticMap(
            800, 600,
            url_template=TILE_URL,
            headers={"User-Agent": USER_AGENT},
        )
        marker = CircleMarker((lon, lat), "#D92B2B", 16)
        m.add_marker(marker)
        img = m.render(zoom=zoom)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return _fallback_map_placeholder()


def _fallback_map_placeholder() -> bytes:
    """Return a simple gray placeholder image if map generation fails."""
    img = Image.new("RGB", (800, 600), color=(230, 230, 230))
    draw = ImageDraw.Draw(img)
    draw.text((350, 280), "Karte nicht verfügbar", fill=(100, 100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_map_page(
    output_doc: fitz.Document,
    data: ProjectData,
    logo_png: bytes | None,
    internal_page_num: int,
    total_pages: int,
) -> fitz.Page:
    """Create and insert a map page into output_doc."""
    page = output_doc.new_page(width=PAGE_W, height=PAGE_H)
    draw_header(page, data, logo_png)
    draw_section_title(page, "Projektstandort – Karte", CONTENT_TOP + 10)

    # Map image area
    map_rect = fitz.Rect(MARGIN_L, CONTENT_TOP + 22, MARGIN_R, FOOTER_Y - 10)

    # Always geocode from the current address fields so that addresses
    # corrected by the user in the confirmation dialog are properly reflected.
    # Pre-set lat/lon on the data object are only used as a last resort.
    lat, lon = None, None
    if data.address_full:
        coords = geocode_address(data.address_full)
        if coords:
            lat, lon = coords

    # Final fallback: use pre-geocoded coordinates if address lookup failed
    if lat is None and data.lat is not None:
        lat, lon = data.lat, data.lon

    if lat is not None and lon is not None:
        map_bytes = generate_map_image(lat, lon)
    else:
        map_bytes = _fallback_map_placeholder()

    if map_bytes:
        page.insert_image(map_rect, stream=map_bytes)
    else:
        page.draw_rect(map_rect, color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9))
        page.insert_text(
            (MARGIN_L + 20, CONTENT_TOP + 100),
            "Kartenansicht nicht verfügbar",
            fontsize=10,
            color=DARK_TEXT,
        )

    # Address label below map – use plz_city and street separately to avoid any
    # extraction artifacts ending up in the label
    location_parts = []
    if data.street:
        location_parts.append(data.street)
    if data.plz_city:
        location_parts.append(data.plz_city)
    if location_parts:
        label = "Standort: " + ", ".join(location_parts)
        page.insert_text(
            (MARGIN_L, FOOTER_Y - 5),
            label,
            fontsize=7,
            color=DARK_TEXT,
            fontname="Helvetica",
        )

    draw_footer(page, internal_page_num, total_pages)
    return page
