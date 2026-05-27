"""
Generate cover page from Deckblatt.pdf template by overlaying variable project data.

The Deckblatt.pdf page is 540x720 pt (not A4). All coordinates below were measured
directly from the PDF using PyMuPDF text extraction.
"""
import fitz
from processor.extractor import ProjectData

# Exact bounding box of the template's sample variable text (measured from A4 PDF).
# Spans x=[468.1..555.5], y=[664.9..743.7] — padded with a few pt on each side.
COVER_TEXT_RECT = fitz.Rect(460, 658, 562, 750)

# Separator line above the PROFINAL SOLAR footer (footer text sits at y≈823.9)
_SEP_Y = 821.0
_SEP_X0 = 11.0
_SEP_X1 = 570.0
_GRAY = (0.75, 0.75, 0.75)

# Right edge of the template text block (all lines are right-aligned here)
_X_RIGHT = 555.5

# Baseline y-positions measured from the PDF (y_bottom of bbox minus ~2pt descender).
# "Projektbericht" has a larger gap below it (heading style); the rest are tightly spaced.
_LINE_Y = [674.0, 697.0, 708.0, 719.0, 731.0, 742.0]


def generate_cover_page(deckblatt_path: str, data: ProjectData, output_doc: fitz.Document) -> fitz.Page:
    """Copy the Deckblatt template into output_doc and overlay real project data."""
    template = fitz.open(deckblatt_path)
    output_doc.insert_pdf(template, from_page=0, to_page=0)
    page = output_doc[-1]
    template.close()

    # Remove the template's sample text via redaction (physically erases content,
    # more reliable than draw_rect which can render behind existing PDF graphics).
    page.add_redact_annot(COVER_TEXT_RECT, fill=(1, 1, 1))
    page.apply_redactions(graphics=True, text=True)

    # Write real project data at exact template positions
    _write_cover_text(page, data)

    # Add separator line above the PROFINAL SOLAR GmbH footer
    page.draw_line(
        fitz.Point(_SEP_X0, _SEP_Y),
        fitz.Point(_SEP_X1, _SEP_Y),
        color=_GRAY,
        width=0.5,
    )

    return page


def _write_cover_text(page: fitz.Page, data: ProjectData):
    """Write the 6 info lines right-aligned at the measured template positions."""
    entries = [
        ("Projektbericht",  8.0, "Helvetica-Bold"),
        (data.date,         8.0, "Helvetica"),
        (data.project_name, 8.0, "Helvetica"),
        (data.plz_city,     8.0, "Helvetica"),
        (data.street,       8.0, "Helvetica"),
        (data.kwp,          8.0, "Helvetica"),
    ]

    for (text, size, font), y in zip(entries, _LINE_Y):
        if not text:
            continue
        tw = fitz.get_text_length(text, fontname=font, fontsize=size)
        page.insert_text(
            (_X_RIGHT - tw, y),
            text,
            fontsize=size,
            fontname=font,
            color=(0.15, 0.15, 0.15),
        )
