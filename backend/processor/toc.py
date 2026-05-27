"""
Generate a Table of Contents page matching the PROFINEXT CI.
"""
import fitz
from processor.ci_helpers import (
    draw_header, draw_footer, draw_section_title,
    MARGIN_L, MARGIN_R, HEADER_H, FOOTER_Y, CONTENT_TOP,
    PAGE_W, PAGE_H, GRAY_LINE, DARK_TEXT, NAVY,
)
from processor.extractor import ProjectData


def generate_toc_page(
    output_doc: fitz.Document,
    page_titles: list[tuple[int, str]],
    data: ProjectData,
    logo_png: bytes | None,
    # Mapping: section_name -> (start_page, end_page) in internal numbering
    # Internal numbering starts at 1 for the TOC page itself
) -> fitz.Page:
    """
    Insert a TOC page into output_doc. Returns the page.

    page_titles: list of (internal_page_number, title) for all pages after the cover.
    """
    page = output_doc.new_page(width=PAGE_W, height=PAGE_H)
    draw_header(page, data, logo_png)
    draw_section_title(page, "Inhaltsverzeichnis", CONTENT_TOP + 10)

    _draw_toc_entries(page, page_titles)

    # Footer: TOC is always internal page 1
    # total_pages is passed in via page_titles metadata (last entry page number)
    total = page_titles[-1][0] if page_titles else 1
    draw_footer(page, 1, total)

    return page


def _draw_toc_entries(page: fitz.Page, entries: list[tuple[int, str]]):
    """
    Draw the TOC entry list.
    entries: [(internal_page_num, title), ...]
    """
    y = CONTENT_TOP + 30
    row_h = 14.0
    dot_char = " "
    x_title = MARGIN_L + 4
    x_num_right = MARGIN_R

    for page_num, title in entries:
        if y > FOOTER_Y - 20:
            break  # no overflow handling for now

        # Separator line (light)
        page.draw_line(
            fitz.Point(MARGIN_L, y + 2),
            fitz.Point(MARGIN_R, y + 2),
            color=(0.9, 0.9, 0.9),
            width=0.3,
        )

        # Title text
        page.insert_text(
            (x_title, y),
            title,
            fontsize=8.5,
            color=DARK_TEXT,
            fontname="Helvetica",
        )

        # Page number (right-aligned)
        num_str = str(page_num)
        tw = fitz.get_text_length(num_str, fontname="Helvetica", fontsize=8.5)
        page.insert_text(
            (x_num_right - tw, y),
            num_str,
            fontsize=8.5,
            color=DARK_TEXT,
            fontname="Helvetica",
        )

        y += row_h
