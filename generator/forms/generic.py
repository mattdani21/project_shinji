import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import qrcode

class BaseFormGenerator:
    def __init__(self, output_dir: str = "data/corpus"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _draw_header_and_qr(self, c, params, title):
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "MERIDIAN WEALTH SOLUTIONS")
        c.setFont("Helvetica", 14)
        c.drawString(50, height - 75, title)
        
        # Draw QR Code (Tier 1 deterministic routing)
        qr_data = f"type:{params['sub_type']};policy:{params.get('policy_number', 'N/A')}"
        qr = qrcode.make(qr_data)
        qr_path = f"/tmp/{params['email_id']}_qr.png"
        qr.save(qr_path)
        c.drawImage(qr_path, width - 150, height - 150, width=100, height=100)
        os.remove(qr_path)
        
    def _draw_signature(self, c, date):
        width, height = A4
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 150, "Declaration and Signature")
        c.setFont("Helvetica", 10)
        c.drawString(50, 130, "I declare that the above information is true and correct.")
        c.drawString(50, 80, "Signature: ___________________________")
        c.drawString(300, 80, f"Date: {date}")

class GenericFormGenerator(BaseFormGenerator):
    def generate(self, params: dict, c: canvas.Canvas = None, save: bool = True) -> str:
        """
        Generates a multi-page form. If 'c' is provided, appends to an existing canvas 
        (useful for broker bulk generation). If save=True, saves and returns the file path.
        """
        file_path = os.path.join(self.output_dir, f"{params['email_id']}_attachment.pdf")
        if c is None:
            c = canvas.Canvas(file_path, pagesize=A4)
            
        width, height = A4
        
        titles = {
            "repurchase": "Repurchase / Withdrawal Form",
            "new_business": "New Business Application",
            "maintenance_client": "Client Details Update Form",
            "maintenance_contrib": "Contribution / Premium Update Form",
            "claim_death": "Death Claim Form",
            "claim_retirement": "Retirement Claim Form"
        }
        
        page_counts = {
            "repurchase": 5,
            "new_business": 4,
            "maintenance_client": 1,
            "maintenance_contrib": 1,
            "claim_death": 3,
            "claim_retirement": 3
        }
        
        sub_type = params.get("sub_type", "repurchase")
        title = titles.get(sub_type, "Insurance Form")
        num_pages = page_counts.get(sub_type, 1)
        
        for page_num in range(1, num_pages + 1):
            if page_num == 1:
                # Page 1 gets Header and QR Code
                self._draw_header_and_qr(c, params, title)
                
                # Draw main details on Page 1
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, height - 150, "Form Details")
                c.setFont("Helvetica", 10)
                
                y_pos = height - 170
                for key, value in params.items():
                    if key not in ["email_id", "sub_type", "main_type"]:
                        label = key.replace("_", " ").title()
                        c.drawString(50, y_pos, f"{label}: {value}")
                        y_pos -= 20
            else:
                # Subsequent pages get basic header
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, f"{title} - Page {page_num}")
                c.setFont("Helvetica", 10)
                c.drawString(50, height - 100, "Terms, Conditions, and Additional Information go here...")
            
            # Signature goes on the LAST page only
            if page_num == num_pages:
                self._draw_signature(c, params.get("date", ""))
                
            # Move to next page in the PDF
            c.showPage()
            
        if save:
            c.save()
            return file_path
        return c
