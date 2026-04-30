import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import qrcode

class RepurchaseFormGenerator:
    def __init__(self, output_dir: str = "data/corpus"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate(self, params: dict) -> str:
        """
        Generates a PDF form and returns the file path.
        """
        file_path = os.path.join(self.output_dir, f"{params['email_id']}_attachment.pdf")
        
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "MERIDIAN WEALTH SOLUTIONS")
        c.setFont("Helvetica", 14)
        c.drawString(50, height - 75, "Repurchase / Withdrawal Form")
        
        # Draw QR Code (Tier 1 deterministic routing)
        # QR contains basic JSON-like info
        qr_data = f"type:repurchase;policy:{params['policy_number']}"
        qr = qrcode.make(qr_data)
        qr_path = f"/tmp/{params['email_id']}_qr.png"
        qr.save(qr_path)
        c.drawImage(qr_path, width - 150, height - 150, width=100, height=100)
        os.remove(qr_path)
        
        # Client Details
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 150, "1. Client Details")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 170, f"Client Name: {params['client_name']}")
        c.drawString(50, height - 190, f"ID Number: {params['id_number']}")
        c.drawString(50, height - 210, f"Policy Number: {params['policy_number']}")
        
        # Repurchase Details
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 250, "2. Withdrawal Request")
        c.setFont("Helvetica", 10)
        
        withdrawal_type = "Full Withdrawal" if params['is_full_withdrawal'] else "Partial Withdrawal"
        c.drawString(50, height - 270, f"Type: {withdrawal_type}")
        
        if not params['is_full_withdrawal']:
            c.drawString(50, height - 290, f"Amount Requested: R {params['repurchase_amount']}")
            
        # Signature block
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 350, "3. Declaration and Signature")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 370, "I declare that the above information is true and correct.")
        c.drawString(50, height - 420, "Signature: ___________________________")
        c.drawString(300, height - 420, f"Date: {params['date']}")
        
        c.save()
        
        return file_path
