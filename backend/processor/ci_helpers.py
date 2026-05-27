"""
Shared CI drawing helpers used by all generated pages.
Colors and layout constants matching the PROFINEXT brand.
"""
import fitz
from pathlib import Path

# Brand colors (r, g, b) in 0-1 range
TEAL = (0.0, 0.608, 0.647)       # #009BA5
NAVY = (0.047, 0.145, 0.380)     # #0C2561
AMBER = (0.961, 0.643, 0.122)    # #F5A31F
GRAY_LINE = (0.75, 0.75, 0.75)
WHITE = (1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0)
DARK_TEXT = (0.15, 0.15, 0.15)

# Page layout (A4 = 595.28 x 841.89 pt)
PAGE_W = 595.28
PAGE_H = 841.89
MARGIN_L = 30.0
MARGIN_R = 565.0
HEADER_H = 72.0       # header area bottom y
FOOTER_Y = 810.0      # footer separator line y (clearly above company text)
CONTENT_TOP = HEADER_H + 12
CONTENT_BOTTOM = FOOTER_Y - 6

# Logo clip rect within a source page (top-left area)
LOGO_CLIP = fitz.Rect(28, 12, 235, 68)


def draw_header(page: fitz.Page, project_data, logo_png: bytes | None = None):
    """Draw PROFINEXT CI header on a page."""
    # White background for header area
    page.draw_rect(fitz.Rect(0, 0, PAGE_W, HEADER_H), color=WHITE, fill=WHITE)

    # Logo (left side) – PROFINAL SOLAR logo, ratio 1020:445 ≈ 2.29:1
    # At 50 pt height → width ≈ 115 pt
    if logo_png:
        logo_rect = fitz.Rect(MARGIN_L, 11, MARGIN_L + 115, 61)
        page.insert_image(logo_rect, stream=logo_png)
    else:
        _draw_text_logo(page)

    # Project info block (right side)
    x_label = 395.0
    x_value = 460.0
    y_start = 14.0
    line_h = 16.0

    rows = [
        ("Projekt", project_data.project_name),
        ("Anlagenleistung", project_data.kwp),
        ("Datum", project_data.date),
    ]
    for i, (label, value) in enumerate(rows):
        y = y_start + i * line_h
        page.insert_text(
            (x_label, y + 10),
            label,
            fontsize=7.5,
            color=DARK_TEXT,
            fontname="Helvetica",
        )
        page.insert_text(
            (x_value, y + 10),
            value,
            fontsize=7.5,
            color=DARK_TEXT,
            fontname="Helvetica-Bold",
        )

    # Separator line below header
    page.draw_line(
        fitz.Point(MARGIN_L, HEADER_H),
        fitz.Point(MARGIN_R, HEADER_H),
        color=GRAY_LINE,
        width=0.5,
    )


# Footer constants — sizes and colors measured directly from Deckblatt.pdf
_FOOTER_SIZE = 9.4          # matches Deckblatt Roboto 9.4 pt
_FOOTER_Y_TEXT = 828.0      # baseline y: far enough below separator so text doesn't overlap
_FOOTER_X_START = MARGIN_L  # left-align with page margin

# "PROFINAL SOLAR GmbH" rendered as color segments (Deckblatt exact colors)
# Dark navy #004577, medium blue #4877b6, amber #f5a228
_C_FOOTER_NAVY  = (0.000, 0.271, 0.467)   # #004577
_C_FOOTER_BLUE  = (0.282, 0.467, 0.714)   # #4877b6
_C_FOOTER_AMBER = (0.961, 0.635, 0.157)   # #f5a228
_C_FOOTER_GRAY  = (0.525, 0.525, 0.533)   # #868688 — contact details

# (text, bold, color) for each segment of the company name
_COMPANY_SEGS = [
    ("PROF",      True,  _C_FOOTER_NAVY),
    ("IN",        True,  _C_FOOTER_BLUE),
    ("AL S",      True,  _C_FOOTER_NAVY),
    ("O",         True,  _C_FOOTER_AMBER),
    ("LAR GmbH",  True,  _C_FOOTER_NAVY),
]
_CONTACT_TEXT = (
    " | Fritz-Keiper-Str. 4, 67822 Mannweiler-Cölln"
    " | Telefon +49 (0)6362 728 99 64"
    " | E-Mail info@profinal.solar"
)


def draw_footer(page: fitz.Page, page_num: int, total_pages: int):
    """Draw Deckblatt-identical footer. Skipped entirely on landscape pages."""
    if page.rect.width > page.rect.height:
        return

    # Page number ABOVE separator line, right-aligned, gray
    page_str = f"Seite {page_num} / {total_pages}"
    tw = fitz.get_text_length(page_str, fontname="Helvetica", fontsize=_FOOTER_SIZE)
    page.insert_text(
        (MARGIN_R - tw, FOOTER_Y - 6),
        page_str,
        fontsize=_FOOTER_SIZE,
        color=_C_FOOTER_GRAY,
        fontname="Helvetica",
    )

    # Separator line (same style as Deckblatt)
    page.draw_line(
        fitz.Point(MARGIN_L, FOOTER_Y),
        fitz.Point(MARGIN_R, FOOTER_Y),
        color=GRAY_LINE,
        width=0.5,
    )

    # Multi-color "PROFINAL SOLAR GmbH" — each segment placed sequentially
    x = _FOOTER_X_START
    for text, bold, color in _COMPANY_SEGS:
        fname = "Helvetica-Bold" if bold else "Helvetica"
        page.insert_text(
            (x, _FOOTER_Y_TEXT),
            text,
            fontsize=_FOOTER_SIZE,
            color=color,
            fontname=fname,
        )
        x += fitz.get_text_length(text, fontname=fname, fontsize=_FOOTER_SIZE)

    # Gray contact details following the company name
    page.insert_text(
        (x, _FOOTER_Y_TEXT),
        _CONTACT_TEXT,
        fontsize=_FOOTER_SIZE,
        color=_C_FOOTER_GRAY,
        fontname="Helvetica",
    )


def draw_section_title(page: fitz.Page, title: str, y: float):
    """Draw amber square marker + section title."""
    sq = 9.0
    sq_x = MARGIN_L
    sq_y = y - sq + 1
    page.draw_rect(
        fitz.Rect(sq_x, sq_y, sq_x + sq, sq_y + sq),
        color=AMBER,
        fill=AMBER,
    )
    page.insert_text(
        (MARGIN_L + sq + 6, y),
        title,
        fontsize=10,
        color=DARK_TEXT,
        fontname="Helvetica",
    )


def _draw_text_logo(page: fitz.Page):
    """Fallback: render text if no logo PNG available."""
    page.insert_text(
        (MARGIN_L, 48),
        "PROFINAL SOLAR",
        fontsize=16,
        color=NAVY,
        fontname="Helvetica-Bold",
    )


def load_logo_from_jpg(jpg_path: str) -> bytes | None:
    """Load the PROFINAL SOLAR logo JPG and return as PNG bytes."""
    try:
        import io
        from PIL import Image
        img = Image.open(jpg_path)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def extract_logo_png(source_pdf_path: str) -> bytes | None:
    """Extract logo PNG from a reference PDF (kept as fallback)."""
    try:
        doc = fitz.open(source_pdf_path)
        page_idx = 1 if len(doc) > 1 else 0
        page = doc[page_idx]
        mat = fitz.Matrix(3, 3)
        pix = page.get_pixmap(matrix=mat, clip=LOGO_CLIP)
        png_bytes = pix.tobytes("png")
        doc.close()
        return png_bytes
    except Exception:
        return None
