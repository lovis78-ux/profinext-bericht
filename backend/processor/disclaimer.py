"""
Build the Disclaimer page with PROFINEXT CI header/footer.
The text content is extracted from Disclaimer.pdf and re-rendered.
"""
import fitz
from processor.ci_helpers import (
    draw_header, draw_footer, draw_section_title,
    MARGIN_L, MARGIN_R, HEADER_H, FOOTER_Y, CONTENT_TOP,
    PAGE_W, PAGE_H, DARK_TEXT, NAVY,
)
from processor.extractor import ProjectData


def generate_disclaimer_page(
    output_doc: fitz.Document,
    disclaimer_pdf_path: str,
    data: ProjectData,
    logo_png: bytes | None,
    internal_page_num: int,
    total_pages: int,
) -> fitz.Page:
    """
    Insert disclaimer page into output_doc.
    Extracts text from disclaimer_pdf_path and renders it in the new CI.
    """
    # Extract disclaimer text blocks from source PDF
    blocks = _extract_disclaimer_blocks(disclaimer_pdf_path)

    page = output_doc.new_page(width=PAGE_W, height=PAGE_H)
    draw_header(page, data, logo_png)
    draw_section_title(
        page,
        "Allgemeine Hinweise – Online-Planungstool (B2B / Fachanwender)",
        CONTENT_TOP + 10,
    )

    _render_disclaimer_text(page, blocks)

    draw_footer(page, internal_page_num, total_pages)
    return page


def _extract_disclaimer_blocks(pdf_path: str) -> list[dict]:
    """Extract text blocks preserving bold/normal distinction.
    Groups all spans within a PDF block into a single paragraph entry."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    blocks = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        all_spans = [
            span
            for line in b.get("lines", [])
            for span in line.get("spans", [])
            if span["text"].strip()
        ]
        if not all_spans:
            continue
        combined_text = " ".join(s["text"].strip() for s in all_spans)
        first = all_spans[0]
        is_bold = "Bold" in first.get("font", "") or bool(first.get("flags", 0) & (2**4))
        blocks.append({"text": combined_text, "bold": is_bold, "size": first["size"]})
    doc.close()
    return blocks


def _insert_line(page, words, x, y, max_w, font, size, color, last_line: bool):
    """Insert one line of text. Justified unless it's the last line of a block."""
    if last_line or len(words) <= 1:
        # Last line or single word: plain left-aligned
        page.insert_text((x, y), " ".join(words), fontsize=size, color=color, fontname=font)
    else:
        # Justify: distribute remaining space evenly between words
        words_width = sum(fitz.get_text_length(w, fontname=font, fontsize=size) for w in words)
        gap = (max_w - words_width) / (len(words) - 1)
        cx = x
        for word in words:
            page.insert_text((cx, y), word, fontsize=size, color=color, fontname=font)
            cx += fitz.get_text_length(word, fontname=font, fontsize=size) + gap


def _render_disclaimer_text(page: fitz.Page, blocks: list[dict]):
    """Render extracted disclaimer blocks onto the page with justified body text."""
    y = CONTENT_TOP + 28
    x = MARGIN_L
    max_w = MARGIN_R - MARGIN_L
    line_h_normal = 10.5
    line_h_heading = 13.0
    after_heading_gap = 2.0   # small gap after a heading, before its body text
    section_gap = 10.0        # blank-line-sized gap BEFORE each new heading

    for i, block in enumerate(blocks):
        text = block["text"]
        is_bold = block["bold"]
        font = "Helvetica-Bold" if is_bold else "Helvetica"
        size = 7.5 if not is_bold else 8.0
        lh = line_h_heading if is_bold else line_h_normal

        # Extra space before every heading except the very first block
        if is_bold and i > 0:
            y += section_gap

        if y > FOOTER_Y - 12:
            break

        # Word-wrap into lines
        words = text.split()
        lines: list[list[str]] = []
        current: list[str] = []
        for word in words:
            test = current + [word]
            tw = fitz.get_text_length(" ".join(test), fontname=font, fontsize=size)
            if tw > max_w and current:
                lines.append(current)
                current = [word]
            else:
                current = test
        if current:
            lines.append(current)

        # Render lines — justify all but the last; headings always left-aligned
        for j, line_words in enumerate(lines):
            last = (j == len(lines) - 1)
            _insert_line(page, line_words, x, y, max_w, font, size, DARK_TEXT,
                         last_line=(last or is_bold))
            y += lh

        y += after_heading_gap if is_bold else 1.5
