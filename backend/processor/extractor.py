import re
import fitz
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProjectData:
    project_name: str = ""
    plz: str = ""
    city: str = ""
    street: str = ""
    date: str = ""
    kwp: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None

    @property
    def address_full(self) -> str:
        parts = []
        if self.street:
            parts.append(self.street)
        if self.plz and self.city:
            parts.append(f"{self.plz} {self.city}")
        elif self.city:
            parts.append(self.city)
        return ", ".join(parts)

    @property
    def plz_city(self) -> str:
        if self.plz and self.city:
            return f"{self.plz} {self.city}"
        return self.city or self.plz


def extract_project_data(pdf_path: str) -> ProjectData:
    doc = fitz.open(pdf_path)
    full_text = ""
    page_texts = []
    for page in doc:
        t = page.get_text()
        full_text += t + "\n"
        page_texts.append(t)
    doc.close()

    data = ProjectData()

    # Projektname
    m = re.search(r'Projektname[:\s]+([^\n\r]+)', full_text)
    if m:
        data.project_name = m.group(1).strip()

    # PLZ + Stadt: In this PDF format, PLZ and city often appear together as
    # "97959 Assamstadt" or "26209 Hatten" without a label, or the labels are on
    # separate lines from the values. Extract the combined pattern first.
    summary_pages = "\n".join(page_texts[:2])
    m = re.search(r'\b(\d{5})\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-]{2,}(?:\s[A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-]+)*)', summary_pages)
    if m:
        data.plz = m.group(1).strip()
        data.city = m.group(2).strip().rstrip(',').strip()
    else:
        # Fallback: label-based extraction (only consume space/tab, NOT newlines,
        # to avoid jumping to the next row's value like "331m" altitude)
        m = re.search(r'Postleitzahl[ \t]*:[ \t]*(\d{4,5})', full_text)
        if m:
            data.plz = m.group(1).strip()
        m = re.search(r'\nStadt[ \t]*:[ \t]*([^\n\r\(]+)', full_text)
        if m:
            val = m.group(1).strip()
            # Reject values that look like altitude (e.g. "331m", "331 m")
            if not re.match(r'^\d+\s*m$', val, re.IGNORECASE):
                data.city = val

    # Straße – only consume space/tab after the colon, not newlines
    m = re.search(r'\nStraße[ \t]*:[ \t]*([^\n\r]+)', full_text)
    if m:
        val = m.group(1).strip()
        if val and val not in ("", "-"):
            data.street = val

    # Datum – try Erstellungsdatum first, then header date pattern
    m = re.search(r'Erstellungsdatum[:\s]+([^\n\r]+)', full_text)
    if m:
        data.date = m.group(1).strip()
    else:
        # Fall back to date in header line like "260518_VD-Alusysteme 20.05.2026"
        m = re.search(r'(\d{2}\.\d{2}\.\d{4})', full_text)
        if m:
            data.date = m.group(1).strip()

    # kWp – In this PDF format the kWp value appears as a standalone line BEFORE
    # the "Nennleistung" label (column-first extraction). Collect all distinct kWp
    # values from the first two summary pages and sum them.
    kwp_total_match = re.search(r'Anlagenleistung\s+Summe[ \t]*:[ \t]*([\d,\.]+)\s*kWp', full_text)
    if kwp_total_match:
        data.kwp = f"{kwp_total_match.group(1).strip()} kWp"
    else:
        summary_text = "\n".join(page_texts[:2])
        kwp_values = re.findall(r'([\d,\.]+)\s*kWp', summary_text)
        if kwp_values:
            unique_vals = list(dict.fromkeys(kwp_values))
            total = sum(float(v.replace(',', '.')) for v in unique_vals)
            formatted = f"{total:.2f}".replace('.', ',')
            data.kwp = f"{formatted} kWp"

    return data


def extract_page_titles(pdf_path: str, project_name: str) -> list[tuple[int, str]]:
    """Return list of (original_page_index, title) for each page."""
    doc = fitz.open(pdf_path)
    titles = []

    for page_idx, page in enumerate(doc):
        text = page.get_text()
        title = _extract_title_from_page(text, project_name)
        titles.append((page_idx, title))

    doc.close()
    return titles


# Text fragments from the old Profinal footer/sidebar that must never become TOC titles
_TITLE_BLOCKLIST = [
    "sitz und registergericht",
    "bankverbindung",
    "ust-idnr",
    "steuer-nr",
    "telefon:",
    "mobil:",
    "e-mail:",
    "planning tool",
]

# Canonical renaming: extracted section name → display name in TOC
_TITLE_RENAMES: dict[str, str] = {
    "Zusammenfassung": "Projektparameter",
    "Materialliste": "Materialstückliste",
}


def _is_blocked_line(line: str) -> bool:
    ll = line.lower()
    return any(bl in ll for bl in _TITLE_BLOCKLIST)


def _extract_title_from_page(page_text: str, project_name: str) -> str:
    lines = [l.strip() for l in page_text.splitlines() if l.strip()]

    # Primary: look for "[Title], [ProjectName]" pattern (appears as page header in the PDF)
    for line in lines[:14]:
        if _is_blocked_line(line):
            continue
        if project_name and project_name in line:
            title = line.split(project_name)[0].strip().rstrip(',').strip()
            if title:
                title = re.sub(r'\s*\d{2}\.\d{2}\.\d{4}\s*$', '', title).strip()
                return _TITLE_RENAMES.get(title, title)

    # Secondary: first non-blocked line that looks like a section title
    for line in lines[:14]:
        if _is_blocked_line(line):
            continue
        if len(line) > 5 and not re.match(r'^\d', line) and '/' not in line:
            if re.search(r'[A-ZÄÖÜa-zäöü]{4,}', line):
                return _TITLE_RENAMES.get(line[:80], line[:80])

    # Fallback: first non-blocked line at all
    for line in lines:
        if not _is_blocked_line(line):
            return _TITLE_RENAMES.get(line[:80], line[:80])

    return "Seite"
