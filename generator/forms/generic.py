"""
Realistic Multi-Page Form Generator for Tessera AI Indexer.

This generator creates forms that reflect the REAL edge cases human indexers face:
- Forms WITH and WITHOUT QR codes (legacy vs modern)
- Multi-page forms with realistic per-page content
- Cover letters prepended by brokers
- Incomplete forms (missing signature pages)
- Mixed Afrikaans/English text
- Poor-quality text (simulated OCR degradation)
"""
import os
import json
import random
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import qrcode


class BaseFormGenerator:
    def __init__(self, output_dir: str = "data/corpus"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _draw_header_and_qr(self, c, params, title, page_num=1, total_pages=1):
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "MERIDIAN WEALTH SOLUTIONS")
        c.setFont("Helvetica", 14)
        c.drawString(50, height - 75, title)
        
        # Draw QR Code (Tier 1 deterministic routing + structural metadata)
        qr_payload = {
            "sub_type": params['sub_type'],
            "policy": params.get('policy_number', 'N/A'),
            "page": page_num,
            "total_pages": total_pages,
            "investor_id": params.get("investor_id", "N/A")
        }
        qr_data = json.dumps(qr_payload)
        qr = qrcode.make(qr_data)
        qr_path = f"/tmp/{params['email_id']}_p{page_num}_qr.png"
        qr.save(qr_path)
        c.drawImage(qr_path, width - 120, height - 120, width=80, height=80)
        os.remove(qr_path)
        
    def _draw_header_no_qr(self, c, params, title):
        """Legacy form header — no QR code, just text."""
        width, height = A4
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "MERIDIAN WEALTH SOLUTIONS")
        c.setFont("Helvetica", 14)
        c.drawString(50, height - 75, title)
        c.setFont("Helvetica", 9)
        c.drawString(50, height - 95, "Form Ref: MWS-{}".format(params.get("sub_type", "GEN").upper()))
        
    def _draw_signature(self, c, date):
        width, height = A4
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 150, "Declaration and Signature")
        c.setFont("Helvetica", 10)
        c.drawString(50, 130, "I declare that the above information is true and correct.")
        c.drawString(50, 80, "Signature: ___________________________")
        c.drawString(300, 80, "Date: {}".format(date))


# ─── Realistic page content per form type ───────────────────────────────

REPURCHASE_PAGES = [
    # Page 1: Client details
    [
        "SECTION A: INVESTOR DETAILS",
        "Full Name: {client_name}",
        "ID Number: {id_number}",
        "Policy Number: {policy_number}",
        "Contact Number: {new_phone}",
        "Email: {new_email}",
    ],
    # Page 2: Withdrawal details
    [
        "SECTION B: WITHDRAWAL / REPURCHASE DETAILS",
        "Type of withdrawal: {withdrawal_type}",
        "Amount requested: R {repurchase_amount}",
        "Reason for withdrawal: Personal financial needs",
        "Tax directive number (if applicable): ___________",
        "Have you received independent financial advice? YES / NO",
    ],
    # Page 3: Banking details
    [
        "SECTION C: BANKING DETAILS FOR PAYMENT",
        "Bank Name: First National Bank",
        "Branch Code: 250655",
        "Account Number: 62XXXXXXXXX",
        "Account Type: Cheque / Savings",
        "Account Holder: {client_name}",
        "",
        "IMPORTANT: We can only pay into an account in the name of the policy holder.",
    ],
    # Page 4: Tax and regulatory
    [
        "SECTION D: TAX IMPLICATIONS",
        "Please note the following tax implications of your withdrawal:",
        "- Withdrawals are subject to income tax per the Income Tax Act.",
        "- A tax directive will be applied for before payment is made.",
        "- Retirement fund withdrawals are taxed per the withdrawal table.",
        "",
        "SECTION E: FICA REQUIREMENTS",
        "Please attach certified copies of:",
        "- South African ID document",
        "- Proof of residential address (not older than 3 months)",
        "- Proof of banking details",
    ],
    # Page 5: Declaration and signature (BOUNDARY MARKER)
    [],  # Empty — signature drawn separately
]

MAINTENANCE_CLIENT_PAGES = [
    # Page 1: All details + signature (1 page form)
    [
        "SECTION A: EXISTING CLIENT DETAILS",
        "Full Name: {client_name}",
        "ID Number: {id_number}",
        "Policy Number: {policy_number}",
        "",
        "SECTION B: UPDATED DETAILS",
        "New Address: {new_address}",
        "New Phone: {new_phone}",
        "New Email: {new_email}",
    ],
]

MAINTENANCE_CONTRIB_PAGES = [
    [
        "SECTION A: POLICY DETAILS",
        "Full Name: {client_name}",
        "ID Number: {id_number}",
        "Policy Number: {policy_number}",
        "",
        "SECTION B: PREMIUM / CONTRIBUTION CHANGE",
        "New Premium Amount: R {new_premium_amount}",
        "Payment Frequency: {payment_frequency}",
        "Effective Date: {date}",
    ],
]

NEW_BUSINESS_PAGES = [
    [
        "SECTION A: APPLICANT DETAILS",
        "Full Name: {client_name}",
        "ID Number: {id_number}",
        "Date of Birth: ___________",
        "Marital Status: ___________",
    ],
    [
        "SECTION B: PRODUCT SELECTION",
        "Product Code: {product_code}",
        "Initial Premium: R {initial_premium}",
        "Payment Frequency: Monthly",
        "Nominated Beneficiary: ___________",
    ],
    [
        "SECTION C: RISK PROFILE",
        "Investment Strategy: Balanced / Aggressive / Conservative",
        "Risk tolerance: Medium",
        "Investment horizon: 10+ years",
    ],
    [],  # Signature page
]

CLAIM_DEATH_PAGES = [
    [
        "SECTION A: CLAIMANT DETAILS",
        "Full Name (Claimant): {client_name}",
        "ID Number: {id_number}",
        "Relationship to Deceased: {relationship}",
    ],
    [
        "SECTION B: DECEASED DETAILS",
        "Full Name (Deceased): {deceased_name}",
        "ID Number (Deceased): {deceased_id}",
        "Date of Death: {date}",
        "Death Certificate Number: {death_certificate_number}",
        "Policy Number: {policy_number}",
        "",
        "Cause of Death: Natural / Unnatural",
        "Place of Death: ___________",
    ],
    [],  # Signature page
]

CLAIM_RETIREMENT_PAGES = [
    [
        "SECTION A: MEMBER DETAILS",
        "Full Name: {client_name}",
        "ID Number: {id_number}",
        "Policy Number: {policy_number}",
        "Date of Retirement: {retirement_date}",
    ],
    [
        "SECTION B: RETIREMENT BENEFIT OPTIONS",
        "Option 1: Full lump sum withdrawal",
        "Option 2: Purchase a living annuity",
        "Option 3: Purchase a guaranteed annuity",
        "Option 4: Combination (specify split)",
        "",
        "Selected option: ___________",
    ],
    [],  # Signature page
]

FORM_PAGES = {
    "repurchase": REPURCHASE_PAGES,
    "maintenance_client": MAINTENANCE_CLIENT_PAGES,
    "maintenance_contrib": MAINTENANCE_CONTRIB_PAGES,
    "new_business": NEW_BUSINESS_PAGES,
    "claim_death": CLAIM_DEATH_PAGES,
    "claim_retirement": CLAIM_RETIREMENT_PAGES,
}

TITLES = {
    "repurchase": "Repurchase / Withdrawal Form",
    "new_business": "New Business Application",
    "maintenance_client": "Client Details Update Form",
    "maintenance_contrib": "Contribution / Premium Update Form",
    "claim_death": "Death Claim Form",
    "claim_retirement": "Retirement Claim Form",
}

# Afrikaans translations for mixed-language edge cases
AFRIKAANS_FILLERS = [
    "Hiermee bevestig ek dat die bogenoemde inligting korrek is.",
    "Alle dokumente moet binne 30 dae ingedien word.",
    "Kontak ons gerus indien u enige navrae het.",
    "Verklaring: Ek, die ondertekenaar, verklaar hiermee dat die inligting waar en korrek is.",
    "Onttrekking sal binne 14 werksdae verwerk word.",
    "Polishouer se handtekening word vereis.",
]

# Cover letter templates (brokers prepend these)
COVER_LETTERS = [
    "Dear Meridian Team,\n\nPlease find attached the completed form(s) for my client. "
    "Kindly process at your earliest convenience.\n\nRegards,\n{broker_name}\nBroker Code: BRK-{broker_code}",
    
    "Hi,\n\nAttached please find documentation for Policy {policy_number}.\n"
    "Please confirm receipt.\n\nThanks,\n{broker_name}",
    
    "To whom it may concern,\n\nI am submitting the following on behalf of my client "
    "{client_name} (ID: {id_number}).\n\nPlease process and revert.\n\n"
    "Kind regards,\n{broker_name}\nFinancial Advisor",
]


class GenericFormGenerator(BaseFormGenerator):
    def generate(self, params: dict, c: canvas.Canvas = None, save: bool = True,
                 has_qr: bool = True, include_cover_letter: bool = False,
                 include_signature: bool = True, mixed_language: bool = False,
                 rng: random.Random = None) -> str:
        """
        Generates a realistic multi-page form.
        
        Args:
            params: Form parameters (client_name, policy_number, etc.)
            c: Optional canvas to append to (for bulk PDFs)
            save: Whether to save the PDF
            has_qr: Whether to include a QR code (False = legacy form)
            include_cover_letter: Whether to prepend a broker cover letter page
            include_signature: Whether to include the signature page (False = incomplete form)
            mixed_language: Whether to inject Afrikaans text
            rng: Random number generator for deterministic randomness
        """
        if rng is None:
            rng = random.Random(42)
            
        file_path = os.path.join(self.output_dir, "{}_attachment.pdf".format(params['email_id']))
        if c is None:
            c = canvas.Canvas(file_path, pagesize=A4)
            
        width, height = A4
        sub_type = params.get("sub_type", "repurchase")
        title = TITLES.get(sub_type, "Insurance Form")
        pages = FORM_PAGES.get(sub_type, [[]])
        
        # --- EDGE CASE: Broker Cover Letter ---
        if include_cover_letter:
            c.setFont("Helvetica", 11)
            template = rng.choice(COVER_LETTERS)
            cover_text = template.format(
                broker_name=rng.choice(["J. van der Merwe", "S. Naidoo", "P. Botha", "M. Dlamini"]),
                broker_code=str(rng.randint(1000, 9999)),
                policy_number=params.get("policy_number", ""),
                client_name=params.get("client_name", ""),
                id_number=params.get("id_number", "")
            )
            y = height - 80
            for line in cover_text.split("\n"):
                c.drawString(50, y, line)
                y -= 18
            c.showPage()
        
        # --- Generate each page ---
        for page_idx, page_lines in enumerate(pages):
            page_num = page_idx + 1
            is_last = page_num == len(pages)
            
            # If this is the signature page and we don't want it, skip generating the page entirely
            if is_last and not include_signature:
                continue
                
            # Draw Header and QR on EVERY page
            if has_qr:
                self._draw_header_and_qr(c, params, title, page_num=page_num, total_pages=len(pages))
            else:
                self._draw_header_no_qr(c, params, title)
            
            # Start Y position for content
            start_y = height - 160
            
            # Draw page content
            y = start_y
            c.setFont("Helvetica", 10)
            for line_template in page_lines:
                # Fill in template variables from params
                try:
                    line = line_template.format(**params)
                except KeyError:
                    line = line_template
                    
                # Bold for section headers
                if line.startswith("SECTION"):
                    c.setFont("Helvetica-Bold", 11)
                    y -= 10  # Extra spacing before sections
                else:
                    c.setFont("Helvetica", 10)
                    
                c.drawString(50, y, line)
                y -= 16
                
            # EDGE CASE: Mixed Afrikaans text
            if mixed_language and not is_last:
                y -= 20
                c.setFont("Helvetica-Oblique", 9)
                c.drawString(50, y, rng.choice(AFRIKAANS_FILLERS))
                y -= 14
            
            # Signature on LAST page only (unless incomplete)
            if is_last and include_signature:
                self._draw_signature(c, params.get("date", ""))
                
            c.showPage()
            
        if save:
            c.save()
            return file_path
        return c
