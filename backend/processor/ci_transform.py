"""
Transform existing "alt-format" planning tool pages to PROFINEXT CI.

Strategy:
  1. White out the old header bar (top ~55pt)
  2. White out the old footer area (bottom strip, size adapted to page orientation)
  3. White out the left sidebar strip (the rotated tool text, ~18pt wide)
  4. Redact any remaining Profinal boilerplate text found anywhere on the page
  5. Draw new CI header (logo + project info + separator)
  6. Draw new CI footer (separator + company info + page number) — portrait only
"""
import fitz
from processor.ci_helpers import (
    draw_header, draw_footer,
    PAGE_W, PAGE_H, HEADER_H, FOOTER_Y,
)
from processor.extractor import ProjectData

# Old Profinal boilerplate text fragments that must be removed wherever they appear.
# These are legal/contact footer texts from the Profinal planning tool template.
_PROFINAL_BOILERPLATE = [
    "Sitz und Registergericht",
    "Bankverbindung",
    "USt-IdNr",
    "Steuer-Nr",
    "Telefon:",
    "Mobil:",
    "E-Mail:",
    "Planning Tool",
    "planning tool",
]


def transform_page(
    src_page: fitz.Page,
    output_doc: fitz.Document,
    data: ProjectData,
    logo_png: bytes | None,
    internal_page_num: int,
    total_pages: int,
) -> fitz.Page:
    """
    Copy src_page into output_doc, apply CI transformation, return new page.
    """
    # Insert source page into output document
    start_idx = len(output_doc)
    output_doc.insert_pdf(src_page.parent, from_page=src_page.number, to_page=src_page.number)
    new_page = output_doc[start_idx]

    pw = new_page.rect.width
    ph = new_page.rect.height
    is_landscape = pw > ph

    # 1. Build redaction rects adapted to actual page dimensions.
    #    Portrait: footer starts at y=792 (last ~50pt).
    #    Landscape: footer is the last 35pt of the shorter dimension.
    header_rect  = fitz.Rect(0, 0, pw, 58)
    footer_start = (ph - 35) if is_landscape else 792
    footer_rect  = fitz.Rect(0, footer_start, pw, ph)
    sidebar_rect = fitz.Rect(0, 0, 19, ph)

    for rect in (header_rect, footer_rect, sidebar_rect):
        new_page.add_redact_annot(rect, fill=(1, 1, 1))

    # 2. Pattern-based redaction: erase Profinal boilerplate anywhere on the page
    #    (catches text that falls outside the fixed structural rects).
    for pattern in _PROFINAL_BOILERPLATE:
        for hit in new_page.search_for(pattern):
            # Expand hit rect by 2 pt on each side (inflate not available in all versions)
            padded = fitz.Rect(hit.x0 - 2, hit.y0 - 2, hit.x1 + 2, hit.y1 + 2)
            new_page.add_redact_annot(padded, fill=(1, 1, 1))

    new_page.apply_redactions(graphics=True, text=True)

    # 3. Apply new CI header and footer
    draw_header(new_page, data, logo_png)
    draw_footer(new_page, internal_page_num, total_pages)

    return new_page


def transform_all_pages(
    src_doc: fitz.Document,
    output_doc: fitz.Document,
    data: ProjectData,
    logo_png: bytes | None,
    start_internal_num: int,
    total_pages: int,
) -> list[str]:
    """
    Transform all pages from src_doc and append to output_doc.
    Returns list of page titles (for TOC building).
    """
    from processor.extractor import _extract_title_from_page
    titles = []
    for i, page in enumerate(src_doc):
        title = _extract_title_from_page(page.get_text(), data.project_name)
        titles.append(title)
        transform_page(
            page,
            output_doc,
            data,
            logo_png,
            start_internal_num + i,
            total_pages,
        )
    return titles
