"""
Main processing pipeline:
  Page 1  – Cover (Deckblatt)
  Page 2  – Inhaltsverzeichnis     (internal Seite 1)
  Page 3  – Disclaimer             (internal Seite 2)
  Page 4  – Map                    (internal Seite 3)
  Page 5+ – CI-transformed report  (internal Seite 4 …)
"""
import fitz
from pathlib import Path

from config import DECKBLATT_PATH, DISCLAIMER_PATH, LOGO_SOURCE_PDF, LOGO_JPG_PATH
from processor.extractor import extract_project_data, ProjectData
from processor.ci_helpers import load_logo_from_jpg, extract_logo_png
from processor.cover import generate_cover_page
from processor.toc import generate_toc_page
from processor.disclaimer import generate_disclaimer_page
from processor.map_gen import generate_map_page, geocode_address
from processor.ci_transform import transform_all_pages


def process_report(
    src_path: str,
    output_path: str,
    override_data: ProjectData | None = None,
) -> ProjectData:
    """
    Full pipeline. Reads src_path, writes to output_path.
    If override_data is provided it is used instead of auto-extraction
    (e.g. after the user confirmed/corrected data in the UI).
    Returns the ProjectData used, for DB storage.
    """
    # ── 1. Extract (or use confirmed) project data ───────────────────────
    data = override_data if override_data is not None else extract_project_data(src_path)

    # Geocode once upfront so map page can reuse the result
    if not data.lat:
        coords = geocode_address(data.address_full)
        if coords:
            data.lat, data.lon = coords

    # ── 2. Load logo PNG ─────────────────────────────────────────────────
    logo_png: bytes | None = None
    if LOGO_JPG_PATH.exists():
        logo_png = load_logo_from_jpg(str(LOGO_JPG_PATH))
    elif LOGO_SOURCE_PDF.exists():
        logo_png = extract_logo_png(str(LOGO_SOURCE_PDF))

    # ── 3. Open source PDF ───────────────────────────────────────────────
    src_doc = fitz.open(src_path)
    src_page_count = len(src_doc)

    # ── 4. Compute total internal page count ────────────────────────────
    # Internal pages = TOC(1) + Disclaimer(1) + Map(1) + src_pages
    total_internal = 3 + src_page_count

    # ── 5. Build output document ─────────────────────────────────────────
    out_doc = fitz.open()

    # Page 1: Cover (no internal page number)
    generate_cover_page(str(DECKBLATT_PATH), data, out_doc)

    # Pages to list in TOC (internal numbering, 1-based, after the TOC page itself)
    # TOC = Seite 1 (itself – not listed)
    # Disclaimer = Seite 2
    # Map = Seite 3
    # Source pages = Seite 4 … (4 + src_page_count - 1)
    toc_entries: list[tuple[int, str]] = [
        (2, "Allgemeine Hinweise"),
        (3, "Projektstandort – Karte"),
    ]

    # We need source page titles for TOC – quick pre-pass
    from processor.extractor import _extract_title_from_page
    for i, page in enumerate(src_doc):
        title = _extract_title_from_page(page.get_text(), data.project_name)
        toc_entries.append((4 + i, title))

    # Page 2: TOC
    generate_toc_page(out_doc, toc_entries, data, logo_png)

    # Page 3: Disclaimer
    generate_disclaimer_page(
        out_doc,
        str(DISCLAIMER_PATH),
        data,
        logo_png,
        internal_page_num=2,
        total_pages=total_internal,
    )

    # Page 4: Map
    generate_map_page(
        out_doc,
        data,
        logo_png,
        internal_page_num=3,
        total_pages=total_internal,
    )

    # Pages 5+: CI-transformed source pages
    transform_all_pages(
        src_doc,
        out_doc,
        data,
        logo_png,
        start_internal_num=4,
        total_pages=total_internal,
    )

    # ── 6. Save ──────────────────────────────────────────────────────────
    out_doc.save(output_path, garbage=4, deflate=True)
    out_doc.close()
    src_doc.close()

    return data
