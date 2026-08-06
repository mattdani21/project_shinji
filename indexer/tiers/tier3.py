"""Tier 3: NER & taxonomy for keyword/policy/ID extraction from unstructured text.

Operates on free text (email bodies, page chunks) where no form structure
exists. Two capabilities:

1. ``extract(text)`` — entity extraction: policy number, SA ID number,
   client name, amounts/dates where present.
2. ``classify(text)`` — sub_type classification from weighted keyword
   evidence (the "taxonomy" half: each sub_type maps to distinctive
   phrases drawn from the taxonomy labels and real corpus language,
   including Afrikaans). Returns an explainable confidence or None when
   there is no evidence, letting Tier 4 take over.

Confidence scheme:
    weighted_hits = sum of keyword weights (strong phrase = 2, weak = 1)
    confidence    = min(0.95, 0.40 + 0.12 * weighted_hits)
  A single strong phrase ("death claim") -> 0.64; three strong signals
  ("death claim" + "deceased" + "death certificate") -> 0.88.
"""
import re
from typing import Dict, List, Optional

# Weighted keyword evidence per sub_type.
# Strong (weight 2): distinctive phrases that alone indicate the form type.
# Weak (weight 1): supporting words.
KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "repurchase": {
        "strong": [
            "repurchase form", "repurchase request", "withdrawal form",
            "withdrawal request", "full repurchase", "partial withdrawal",
            "surrender the full policy", "onttrekking", "onttrek",
        ],
        "weak": ["withdraw", "withdrawal", "repurchase", "surrender", "tax directive"],
    },
    "maintenance_client": {
        "strong": [
            "client details update", "change of details", "update my personal details",
            "update my contact information", "update my records", "my details have changed",
            "adres verander", "new address",
        ],
        "weak": ["relocated", "personal details", "contact information", "update my details"],
    },
    "maintenance_contrib": {
        "strong": [
            "premium contribution", "premium adjustment", "contribution change",
            "premium update form", "increase my premium", "change my premium",
            "premie verhoog", "new premium amount",
        ],
        "weak": ["contribution", "premium", "payment frequency"],
    },
    "new_business": {
        "strong": [
            "new business application", "new investment", "open a new",
            "signed application form", "completed application", "nuwe besigheid",
        ],
        "weak": ["application", "initial premium", "product code", "fica"],
    },
    "claim_death": {
        "strong": [
            "death claim", "death benefit", "death certificate", "passed away",
            "lodge a death claim", "sterfte", "overledene",
        ],
        "weak": ["deceased", "policyholder", "life assured", "death"],
    },
    "claim_retirement": {
        "strong": [
            "retirement claim", "retirement benefit", "retirement date",
            "retiring on", "retirement benefit claim", "aftrede",
        ],
        "weak": ["retiring", "retire", "retirement", "lump sum", "annuity"],
    },
}

_POLICY_RE = re.compile(r"(?:POL-)?\d{8,12}\b")
_POLICY_LABEL_RE = re.compile(r"(?:policy|reference)\s*(?:number)?\s*[#:]\s*((?:POL-)?\d{8,12})\b", re.IGNORECASE)
_ID_RE = re.compile(r"\b\d{13}\b")
_AMOUNT_RE = re.compile(r"R\s?([\d][\d\s,\.]*)")
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_CLOSING_RE = re.compile(r"(?:regards|thanks|cheers|thank you)[,\s]*?\n([A-Z][A-Za-z\s\.'-]{2,40})$", re.MULTILINE | re.IGNORECASE)


class Tier3NERExtractor:
    """NER + keyword/taxonomy classification over unstructured text."""

    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence

    # ── public API ────────────────────────────────────────────────────────

    def extract(self, text: str) -> Dict[str, str]:
        """Extract entities from free text (policy/ID/name/amount/date)."""
        fields: Dict[str, str] = {}

        m = _POLICY_LABEL_RE.search(text)
        if m:
            fields["policy_number"] = m.group(1)
        else:
            m = _POLICY_RE.search(text)
            if m and len(m.group(0).replace("POL-", "")) >= 8:
                fields["policy_number"] = m.group(0)

        m = _ID_RE.search(text)
        if m:
            fields["id_number"] = m.group(0)

        m = _AMOUNT_RE.search(text)
        if m:
            fields["amount"] = m.group(1).strip()

        m = _DATE_RE.search(text)
        if m:
            fields["date"] = m.group(0)

        m = _CLOSING_RE.search(text)
        if m:
            fields["client_name"] = m.group(1).strip().splitlines()[0].strip()
        return fields

    def classify(self, text: str) -> Optional[dict]:
        """Classify free text by weighted keyword evidence.

        Returns None when there is no evidence (caller falls through to
        Tier 4), or a dict:
            {tier: 3, prediction, confidence, method: "tier3_ner",
             evidence: {sub_type: [matched phrases]},
             extracted_fields: {...}}
        """
        lower = text.lower()
        evidence: Dict[str, List[str]] = {}
        weighted: Dict[str, int] = {}

        for sub_type, kws in KEYWORDS.items():
            hits = []
            weight = 0
            for phrase in kws["strong"]:
                if phrase in lower:
                    hits.append(phrase)
                    weight += 2
            for phrase in kws["weak"]:
                if phrase in lower:
                    hits.append(phrase)
                    weight += 1
            if hits:
                evidence[sub_type] = hits
                weighted[sub_type] = weight

        if not weighted:
            return None

        best = max(weighted, key=lambda k: weighted[k])
        confidence = min(0.95, 0.40 + 0.12 * weighted[best])
        if confidence < self.min_confidence:
            return None

        return {
            "tier": 3,
            "prediction": best,
            "confidence": round(confidence, 4),
            "method": "tier3_ner",
            "evidence": evidence,
            "extracted_fields": self.extract(text),
        }


if __name__ == "__main__":
    import json
    import sys

    ner = Tier3NERExtractor()
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    print(json.dumps(ner.classify(text), indent=2))
