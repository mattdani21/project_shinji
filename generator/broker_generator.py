import os
import random
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from generator.parameters import ParameterGenerator
from generator.forms.generic import GenericFormGenerator

class BrokerGenerator:
    def __init__(self, output_dir: str = "data/corpus"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.param_gen = ParameterGenerator(seed=123)
        self.form_gen = GenericFormGenerator(output_dir=self.output_dir)
        self._rng = random.Random(123)
        
    def generate_bulk_instruction(self, email_id: str, num_clients: int = 3) -> dict:
        """
        Generates a single email with a single multi-page PDF attachment 
        containing multiple different client forms.
        """
        pdf_path = os.path.join(self.output_dir, f"{email_id}_bulk_attachment.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        
        client_params = []
        body_text = f"Dear Meridian,\n\nPlease find attached the completed forms for {num_clients} of my clients.\n\n"
        
        for i in range(num_clients):
            # Generate random params for each client
            params = self.param_gen.generate_random()
            # Override email_id so QR codes map to this bulk email
            params["email_id"] = f"{email_id}_client{i}"
            client_params.append(params)
            
            # Add to body text
            body_text += f"- {params.get('client_name', 'Client')} (Policy {params.get('policy_number')}): {params.get('sub_type').replace('_', ' ').title()}\n"
            
            # Append this client's multi-page form to the single PDF canvas
            self.form_gen.generate(params, c=c, save=False)
            
        c.save()
        body_text += "\nPlease process these as soon as possible.\n\nRegards,\nBroker"
        
        # Save body
        body_path = os.path.join(self.output_dir, f"{email_id}_body.txt")
        with open(body_path, "w") as f:
            f.write(body_text)
            
        return {
            "email_id": email_id,
            "main_type": "broker_comms",
            "sub_type": "bulk_instructions",
            "body_path": body_path,
            "attachment_path": pdf_path,
            "clients": client_params
        }

if __name__ == "__main__":
    gen = BrokerGenerator(output_dir="data/test_broker")
    res = gen.generate_bulk_instruction("broker_test_001", num_clients=3)
    print(f"Generated Broker Bulk Email: {res['email_id']}")
    print(f"Body saved to: {res['body_path']}")
    print(f"Attachment saved to: {res['attachment_path']}")
    print(f"Contains {len(res['clients'])} clients.")
