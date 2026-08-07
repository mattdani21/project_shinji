"""Tier 2: OCR & Template Matching for standard forms without QR codes.

Legacy forms (no QR) still have a deterministic visual/text structure:
every Meridian form page carries a header ("MERIDIAN WEALTH SOLUTIONS" +
form title + "Form Ref: MWS-<TYPE>"), section markers ("SECTION A: …"),
and known field labels. Tier 2 matches those signals against a template
registry built from the taxonomy and the form generator's layout, and
returns a sub_type with an explainable confidence.

Scanned (image-only) PDFs with no text layer are handled by an optional
OCR hook (pytesseract) when installed; otherwise they are reported as
unreadable and fall through to later tiers.

Confidence scheme (deterministic, explainable):
  - exact Form Ref code hit  -> 0.95 (the form declares its own type)
  - title match (header)     -> base 0.60 + 0.05 per section marker (cap 0.90)
  - sections/fields only     -> 0.30 + 0.05 * sections (cap 0.70) + 0.02 * fields
  - no signals               -> None (no match; caller falls through)
"""
import json
import re
from typing import Dict, List, Optional, Tuple

_NORM_RE = re.compile(r"\s+")
_FORM_REF_RE = re.compile(r"FORM REF: MWS-([A-Z_0-9]+)")
_SIGNATURE_MARKER = "DECLARATION AND SIGNATURE"

# Template registry: per sub_type, the signals a standard form carries.
# Sections/fields are matched as uppercase substrings of normalized text.
TEMPLATES: Dict[str, Dict[str, object]] = {
    "repurchase": {
        "form_ref": "MWS-REPURCHASE",
        "title": "REPURCHASE / WITHDRAWAL FORM",
        "sections": [
            "SECTION A: INVESTOR DETAILS",
            "SECTION B: WITHDRAWAL / REPURCHASE DETAILS",
            "SECTION C: BANKING DETAILS FOR PAYMENT",
            "SECTION D: TAX IMPLICATIONS",
            "SECTION E: FICA REQUIREMENTS",
        ],
        "fields": [
            "POLICY NUMBER:",
            "ID NUMBER:",
            "FULL NAME:",
            "AMOUNT REQUESTED:",
            "ACCOUNT HOLDER:",
            "BANK NAME:",
        ],
    },
    "maintenance_client": {
        "form_ref": "MWS-MAINTENANCE_CLIENT",
        "title": "CLIENT DETAILS UPDATE FORM",
        "sections": [
            "SECTION A: EXISTING CLIENT DETAILS",
            "SECTION B: UPDATED DETAILS",
        ],
        "fields": [
            "POLICY NUMBER:",
            "ID NUMBER:",
            "FULL NAME:",
            "NEW ADDRESS:",
            "NEW PHONE:",
            "NEW EMAIL:",
        ],
    },
    "maintenance_contrib": {
        "form_ref": "MWS-MAINTENANCE_CONTRIB",
        "title": "CONTRIBUTION / PREMIUM UPDATE FORM",
        "sections": [
            "SECTION A: POLICY DETAILS",
            "SECTION B: PREMIUM / CONTRIBUTION CHANGE",
        ],
        "fields": [
            "POLICY NUMBER:",
            "ID NUMBER:",
            "FULL NAME:",
            "NEW PREMIUM AMOUNT:",
            "PAYMENT FREQUENCY:",
        ],
    },
    "new_business": {
        "form_ref": "MWS-NEW_BUSINESS",
        "title": "NEW BUSINESS APPLICATION",
        "sections": [
            "SECTION A: APPLICANT DETAILS",
            "SECTION B: PRODUCT SELECTION",
            "SECTION C: RISK PROFILE",
        ],
        "fields": [
            "ID NUMBER:",
            "FULL NAME:",
            "PRODUCT CODE:",
            "INITIAL PREMIUM:",
            "PAYMENT FREQUENCY:",
        ],
    },
    "claim_death": {
        "form_ref": "MWS-CLAIM_DEATH",
        "title": "DEATH CLAIM FORM",
        "sections": [
            "SECTION A: CLAIMANT DETAILS",
            "SECTION B: DECEASED DETAILS",
        ],
        "fields": [
            "POLICY NUMBER:",
            "ID NUMBER:",
            "FULL NAME (CLAIMANT):",
            "RELATIONSHIP TO DECEASED:",
            "DATE OF DEATH:",
        ],
    },
    "claim_retirement": {
        "form_ref": "MWS-CLAIM_RETIREMENT",
        "title": "RETIREMENT CLAIM FORM",
        "sections": [
            "SECTION A: MEMBER DETAILS",
            "SECTION B: RETIREMENT BENEFIT OPTIONS",
        ],
        "fields": [
            "POLICY NUMBER:",
            "ID NUMBER:",
            "FULL NAME:",
            "DATE OF RETIREMENT:",
            "SELECTED OPTION:",
        ],
    },
}

# Entity regexes for field extraction from matched forms (Tier 3-lite)
_POLICY_RE = re.compile(r"(?:POL-)?\d{8,12}")
_ID_RE = re.compile(r"\b\d{13}\b")
_AMOUNT_RE = re.compile(r"R\s?([\d][\d\s,\.]*)")


def _norm(text: str) -> str:
    return _NORM_RE.sub(" ", text.upper()).strip()


def _extract_fields(text: str) -> Dict[str, str]:
    """Pull policy number, ID number, client name and amounts from form text.

    Label-aware: values are read from their labeled lines ("Policy Number: …",
    "ID Number: …") before falling back to pattern scans, so a 12-digit ID
    can't be mistaken for a policy number.
    """
    fields: Dict[str, str] = {}
    m = re.search(r"POLICY NUMBER\s*:\s*((?:POL-)?\d{8,12})", text, re.IGNORECASE)
    if m:
        fields["policy_number"] = m.group(1)
    else:
        m = re.search(r"POL-\d{8,12}", text, re.IGNORECASE)
        if m:
            fields["policy_number"] = m.group(0)
        else:
            m = re.search(r"(?<!\d)\d{8,12}(?!\d)", text)
            if m:
                fields["policy_number"] = m.group(0)
    m = re.search(r"ID NUMBER\s*:\s*(\d{10,13})", text, re.IGNORECASE)
    if m:
        fields["id_number"] = m.group(1)
    else:
        m = re.search(r"\b\d{13}\b", text)
        if m:
            fields["id_number"] = m.group(0)
    m = re.search(r"(?:FULL NAME \(CLAIMANT\)|FULL NAME|ACCOUNT HOLDER|CLIENT NAME)\s*:\s*([^\n]+)", text, re.IGNORECASE)
    if m:
        fields["client_name"] = m.group(1).strip()
    m = _AMOUNT_RE.search(text)
    if m:
        fields["amount"] = m.group(1).strip()
    return fields


class Tier2TemplateMatcher:
    """Matches standard (legacy, QR-less) forms by text/template signals."""

    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence

    # ── public API ────────────────────────────────────────────────────────

    def match_pdf(self, pdf_path: str) -> Optional[dict]:
        """Extract text (OCR fallback) and match templates. Returns a result
        dict or None when nothing matches."""
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        pages_text: List[str] = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            pages_text.append(page.get_text() or "")
        doc.close()

        combined = "\n".join(pages_text)

        # Scanned PDF: no text layer anywhere -> optional OCR pass
        if not combined.strip():
            ocr_text = self._ocr_pdf(pdf_path)
            if ocr_text is None:
                return None
            combined = ocr_text
            pages_text = [combined]

        signature_count = combined.upper().count(_SIGNATURE_MARKER)
        return self.match_text(
            combined,
            page_count=len(pages_text),
            signature_count=signature_count,
        )

    def match_text(self, text: str, page_count: int = 1,
                   signature_count: int = 1) -> Optional[dict]:
        """Score every template against normalized text."""
        norm = _norm(text)
        scores = {}
        matched_signals = {}

        for sub_type, tpl in TEMPLATES.items():
            conf, signals = self._score_template(norm, tpl)
            if conf is not None:
                scores[sub_type] = conf
                matched_signals[sub_type] = signals

        if not scores:
            return None

        best = max(scores, key=scores.get)
        confidence = scores[best]
        if confidence < self.min_confidence:
            return None

        result = {
            "tier": 2,
            "sub_type": best,
            "confidence": round(confidence, 4),
            "method": "tier2_template",
            "matched_signals": matched_signals[best],
            "extracted_fields": _extract_fields(text),
            "page_count": page_count,
            "signature_count": signature_count,
        }

        # Completeness semantics mirror Tier 1: unsigned forms need review
        if signature_count < 1:
            result["status"] = "incomplete"
            result["rfi_note"] = "No 'Declaration and Signature' marker found — form may be unsigned or missing pages."
            result["confidence"] = round(min(confidence, 0.8), 4)
        else:
            result["status"] = "complete"
        return result

    # ── internals ─────────────────────────────────────────────────────────

    def _score_template(self, norm: str, tpl: dict) -> Optional[Tuple[Optional[float], List[str]]]:
        """Return (confidence, matched signals) per the scheme in the docstring."""
        signals: List[str] = []

        m = _FORM_REF_RE.search(norm)
        if m and m.group(1) == tpl["form_ref"].replace("MWS-", ""):
            return 0.95, ["form_ref"]

        title_hit = tpl["title"] in norm
        sections_hit = [s for s in tpl["sections"] if s in norm]
        fields_hit = [f for f in tpl["fields"] if f in norm]

        if title_hit:
            conf = 0.60 + 0.05 * len(sections_hit)
            signals.append("title")
        elif sections_hit:
            conf = 0.30 + 0.05 * len(sections_hit)
        else:
            # No title and no sections: field labels alone are weak evidence
            if not fields_hit:
                return None, []
            conf = 0.20 + 0.02 * len(fields_hit)

        conf = min(conf, 0.90)
        if title_hit:
            conf = min(conf + 0.02 * len(fields_hit), 0.90)
        else:
            conf = min(conf + 0.02 * len(fields_hit), 0.70)

        signals.extend(sections_hit)
        signals.extend(fields_hit)
        return conf, signals

    def _ocr_pdf(self, pdf_path: str) -> Optional[str]:
        """OCR a scanned PDF via pytesseract (optional dependency).

        Returns None when pytesseract/tesseract is not available.
        """
        try:
            import fitz
            import pytesseract
            from PIL import Image
        except ImportError:
            return None

        try:
            doc = fitz.open(pdf_path)
            chunks = []
            for i in range(len(doc)):
                pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.frombytes("RGB", (pix.w, pix.h), pix.samples)
                chunks.append(pytesseract.image_to_string(img))
            doc.close()
            return "\n".join(chunks)
        except Exception:
            return None


if __name__ == "__main__":
    import sys

    matcher = Tier2TemplateMatcher()
    res = matcher.match_pdf(sys.argv[1])
    print(json.dumps(res, indent=2))
