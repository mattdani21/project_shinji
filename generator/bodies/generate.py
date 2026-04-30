import os
import json
import time
import random
import requests

class BodyGenerator:
    """
    IMPORTANT COMPLIANCE NOTE: 
    This generator uses Gemini Flash to produce synthetic email bodies. 
    It only ever touches FICTIONAL data — invented investor names, fake ID numbers, 
    fictional Meridian Wealth Solutions branding. 
    No real customer mail is ever sent to any external API at any point in this pipeline. 
    This is data generation, not classification.
    At inference time (indexer/), no external API is ever called.
    """
    def __init__(self, delay_seconds: float = 2.0, max_retries: int = 3, use_api: bool = False):
        self.api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyB-t0nFrV4ITCzjA1D7W46jfp0XVgcgtZE")
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={self.api_key}"
        self.delay = delay_seconds
        self.max_retries = max_retries
        self.use_api = use_api
        self._call_count = 0
        self._rng = random.Random(42)
        
    def generate(self, params: dict, messy: bool = False) -> str:
        if messy:
            return self._generate_messy(params)
        if self.use_api:
            return self._generate_api(params)
        return self._generate_template(params)
    
    def _generate_api(self, params: dict) -> str:
        prompt_details = {
            "sub_type": params["sub_type"],
            "client_name": params.get("client_name", "Client"),
            "policy_number": params.get("policy_number", "N/A"),
        }
        
        prompt = f"""Write a short, realistic email from a South African insurance client to their broker or insurance company.
Form Type: {params['sub_type']}
Details: {json.dumps(prompt_details)}

Rules:
- Brief, slightly informal but professional tone
- Mention they have attached the signed form
- Do NOT include a subject line
- Just write the email body text
- Vary the style — some people write formally, some casually
- Include the policy number naturally in the text"""
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.8, "maxOutputTokens": 500}
        }
        
        self._call_count += 1
        if self._call_count > 1:
            time.sleep(self.delay)
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
                if response.status_code == 429:
                    wait = (2 ** attempt) * 2
                    print(f"  Rate limited. Retrying in {wait}s...")
                    last_error = Exception("Rate limited (429)")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep((2 ** attempt) * 2)
                    continue
        
        print(f"  API failed: {last_error}. Using template.")
        return self._generate_template(params)

    def _generate_template(self, params: dict) -> str:
        sub = params["sub_type"]
        name = params.get("client_name", "Client")
        pol = params.get("policy_number", "N/A")
        
        # Pick random greeting, closing, and body style for variety
        greetings = [
            "Hi,", "Hello,", "Good day,", "Hi there,", "Dear Sir/Madam,", 
            "Good morning,", "Good afternoon,", f"Dear Team,", "To whom it may concern,"
        ]
        closings = [
            f"Regards,\n{name}", f"Kind regards,\n{name}", f"Thanks,\n{name}",
            f"Best regards,\n{name}", f"Warm regards,\n{name}", f"Many thanks,\n{name}",
            f"Cheers,\n{name}", f"Thank you,\n{name}"
        ]
        
        greeting = self._rng.choice(greetings)
        closing = self._rng.choice(closings)
        
        generators = {
            "repurchase": self._repurchase_body,
            "new_business": self._new_business_body,
            "maintenance_client": self._maintenance_client_body,
            "maintenance_contrib": self._maintenance_contrib_body,
            "claim_death": self._claim_death_body,
            "claim_retirement": self._claim_retirement_body,
        }
        
        body = generators.get(sub, self._generic_body)(params)
        return f"{greeting}\n\n{body}\n\n{closing}"

    def _repurchase_body(self, p: dict) -> str:
        pol = p["policy_number"]
        is_full = p.get("is_full_withdrawal")
        amt = p.get("repurchase_amount", 0)
        amt_str = f"R {amt:,.2f}" if amt else "R 0.00"
        w_type = "full" if is_full else "partial"
        templates = [
            f"I would like to request a {w_type} withdrawal from my policy {pol}. Please find the completed and signed repurchase form attached. Could you kindly confirm receipt and let me know the expected processing time?",
            f"Please process the attached repurchase form for my investment policy {pol}. I am looking to {'fully withdraw' if is_full else f'withdraw {amt_str} from'} my policy. I have signed where required.",
            f"I've attached the signed withdrawal form for policy {pol}. {'This is for a full repurchase of the policy.' if is_full else f'I need to withdraw {amt_str} as a partial repurchase.'} Please advise on the timeline.",
            f"Further to our phone conversation, I am submitting my repurchase request for policy number {pol}. The signed form is attached. {'I would like to surrender the full policy.' if is_full else f'The partial withdrawal amount is {amt_str}.'} Please confirm once received.",
            f"Attached is the completed withdrawal form for {pol}. I need to access {'the full value' if is_full else amt_str} from my GIA investment due to personal circumstances. Let me know if anything else is needed from my side.",
        ]
        return self._rng.choice(templates)

    def _new_business_body(self, p: dict) -> str:
        pol = p["policy_number"]
        templates = [
            f"Please find attached my completed new business application. My broker has advised me to go with product {p.get('product_code', 'N/A')} with an initial premium of R {p.get('initial_premium', 0):,.2f}. My reference number is {pol}. Let me know if you need any additional documentation.",
            f"I'm excited to be starting my new investment with Meridian. Attached is the signed application form for a {p.get('product_code', 'N/A')} policy with a monthly premium of R {p.get('initial_premium', 0):,.2f}. Policy reference: {pol}.",
            f"As discussed with my financial advisor, I'd like to open a new {p.get('product_code', 'N/A')} policy. The completed application is attached along with my FICA documents. Initial premium: R {p.get('initial_premium', 0):,.2f}. Reference: {pol}.",
            f"Herewith my new business application for product {p.get('product_code', 'N/A')}. I will be contributing R {p.get('initial_premium', 0):,.2f} monthly. All forms are signed and my ID copy is included. Policy number assigned: {pol}.",
        ]
        return self._rng.choice(templates)

    def _maintenance_client_body(self, p: dict) -> str:
        pol = p["policy_number"]
        templates = [
            f"I have recently moved and need to update my personal details on policy {pol}. My new address is {p.get('new_address', 'N/A')}. The completed change of details form is attached.",
            f"Please update my contact information on file for policy number {pol}. I've attached the signed maintenance form with my new details. My updated email is {p.get('new_email', 'N/A')} and my new phone number is {p.get('new_phone', 'N/A')}.",
            f"Kindly note that my details have changed. I need to update my records on policy {pol}. New address: {p.get('new_address', 'N/A')}. I've completed and signed the required form — see attached.",
            f"I'm writing to request an update to my personal information linked to {pol}. I've relocated to {p.get('new_address', 'N/A')}. The signed client details update form is attached for processing.",
        ]
        return self._rng.choice(templates)

    def _maintenance_contrib_body(self, p: dict) -> str:
        pol = p["policy_number"]
        templates = [
            f"I would like to increase my premium contribution on policy {pol} to R {p.get('new_premium_amount', 0):,.2f} per {p.get('payment_frequency', 'month').lower()}. The signed premium adjustment form is attached.",
            f"Please process the attached contribution change form for policy {pol}. I wish to adjust my premium to R {p.get('new_premium_amount', 0):,.2f} {p.get('payment_frequency', 'monthly').lower()}. Let me know once this has been updated.",
            f"Following my review meeting with my advisor, I'd like to change my premium on {pol}. New amount: R {p.get('new_premium_amount', 0):,.2f} ({p.get('payment_frequency', 'Monthly')}). Attached is the completed form.",
            f"Herewith the premium update form for my policy {pol}. I'd like to change my contribution to R {p.get('new_premium_amount', 0):,.2f} on a {p.get('payment_frequency', 'monthly').lower()} basis effective immediately.",
        ]
        return self._rng.choice(templates)

    def _claim_death_body(self, p: dict) -> str:
        pol = p["policy_number"]
        templates = [
            f"I am writing to submit a death claim under policy {pol}. The policyholder, {p.get('deceased_name', 'the deceased')}, has passed away. I have attached the completed claim form along with the death certificate (reference {p.get('death_certificate_number', 'N/A')}). I am the nominated beneficiary.",
            f"It is with great sadness that I inform you of the passing of {p.get('deceased_name', 'the policyholder')}. I need to lodge a death claim on policy number {pol}. The death certificate number is {p.get('death_certificate_number', 'N/A')}. Please find all required forms attached.",
            f"I would like to claim the death benefit on policy {pol} following the death of {p.get('deceased_name', 'the life assured')}. Death certificate: {p.get('death_certificate_number', 'N/A')}. I have attached the completed forms and certified copies of required documents.",
        ]
        return self._rng.choice(templates)

    def _claim_retirement_body(self, p: dict) -> str:
        pol = p["policy_number"]
        templates = [
            f"I am reaching my retirement date of {p.get('retirement_date', 'N/A')} and would like to claim my retirement benefits under policy {pol}. Please find the completed retirement claim form attached. Kindly advise on the process and expected timelines.",
            f"This serves to notify you that I will be retiring on {p.get('retirement_date', 'N/A')}. I would like to commence the retirement benefit claim process for policy {pol}. The signed claim form is attached along with my bank details for payment.",
            f"As per my retirement date of {p.get('retirement_date', 'N/A')}, I am submitting my retirement claim for policy number {pol}. All required documentation is attached. Please let me know if anything further is needed.",
        ]
        return self._rng.choice(templates)

    def _generic_body(self, p: dict) -> str:
        return f"Please find attached my completed form for policy {p.get('policy_number', 'N/A')}. Let me know if you need anything else."

    def _generate_messy(self, params: dict) -> str:
        body = self._generate_template(params)
        # 1. Random typos
        chars = "abcdefghijklmnopqrstuvwxyz"
        for _ in range(5):
            idx = self._rng.randint(0, len(body) - 1)
            body = body[:idx] + self._rng.choice(chars) + body[idx+1:]
        
        # 2. Add some "messy" filler
        filler = [
            " Sorry for the bad handwriting.",
            " My internet is very slow today.",
            " I am sending this from my phone.",
            " Pls help me urgently.",
            " I hope this is the right email address."
        ]
        body += self._rng.choice(filler)
        return body

    def _generate_ambiguous(self) -> str:
        templates = [
            "Hi, I moved to a new house and also want to withdraw all my money from my policy POL-12345678. Attached are both forms.",
            "Dear Meridian, I am retiring soon but my wife also passed away. Here are the claim forms for policy POL-99999999.",
            "Hello, I need to update my phone number and also increase my premium on POL-00001111."
        ]
        return self._rng.choice(templates)
