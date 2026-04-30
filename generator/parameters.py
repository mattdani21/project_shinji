import random
import uuid
import datetime

class ParameterGenerator:
    def __init__(self, seed: int = 42):
        self.random = random.Random(seed)
        
        self.first_names = ["John", "Jane", "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi"]
        self.last_names = ["Smith", "Doe", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez"]
        
    def _generate_sa_id(self) -> str:
        # Format: YYMMDDSSSSCAZ
        year = self.random.randint(40, 99)
        month = self.random.randint(1, 12)
        day = self.random.randint(1, 28)
        seq = self.random.randint(0, 9999)
        c = self.random.choice([0, 1])
        a = 8 # SA citizen
        z = self.random.randint(0, 9)
        return f"{year:02d}{month:02d}{day:02d}{seq:04d}{c}{a}{z}"
        
    def _generate_policy_number(self) -> str:
        return f"POL-{self.random.randint(10000000, 99999999)}"

    def _base_params(self, sub_type: str) -> dict:
        return {
            "email_id": str(uuid.uuid4()),
            "investor_id": f"INV-{self.random.randint(100000, 999999)}",
            "sub_type": sub_type,
            "client_name": f"{self.random.choice(self.first_names)} {self.random.choice(self.last_names)}",
            "id_number": self._generate_sa_id(),
            "policy_number": self._generate_policy_number(),
            "date": (datetime.datetime.now() - datetime.timedelta(days=self.random.randint(0, 30))).strftime("%Y-%m-%d")
        }
        
    def generate_repurchase(self) -> dict:
        params = self._base_params("repurchase")
        params["main_type"] = "policy_admin"
        is_full = self.random.choice([True, False])
        params["is_full_withdrawal"] = is_full
        params["repurchase_amount"] = None if is_full else round(self.random.uniform(1000, 50000), 2)
        return params

    def generate_new_business(self) -> dict:
        params = self._base_params("new_business")
        params["main_type"] = "new_business"
        params["initial_premium"] = round(self.random.uniform(500, 10000), 2)
        params["product_code"] = self.random.choice(["PROD-A", "PROD-B", "PROD-C", "PROD-D"])
        return params

    def generate_maintenance_client(self) -> dict:
        params = self._base_params("maintenance_client")
        params["main_type"] = "policy_admin"
        params["new_address"] = f"{self.random.randint(1, 999)} {self.random.choice(['Main', 'Oak', 'Pine', 'Maple'])} St, {self.random.choice(['Cape Town', 'Johannesburg', 'Durban', 'Pretoria'])}"
        params["new_phone"] = f"0{self.random.randint(60, 89)} {self.random.randint(100, 999)} {self.random.randint(1000, 9999)}"
        params["new_email"] = f"{params['client_name'].replace(' ', '.').lower()}@example.com"
        return params

    def generate_maintenance_contrib(self) -> dict:
        params = self._base_params("maintenance_contrib")
        params["main_type"] = "policy_admin"
        params["new_premium_amount"] = round(self.random.uniform(500, 5000), 2)
        params["payment_frequency"] = self.random.choice(["Monthly", "Quarterly", "Annually"])
        return params

    def generate_claim_death(self) -> dict:
        params = self._base_params("claim_death")
        params["main_type"] = "claims"
        params["deceased_name"] = f"{self.random.choice(self.first_names)} {self.random.choice(self.last_names)}"
        params["death_certificate_number"] = f"DC-{self.random.randint(100000, 999999)}"
        params["beneficiary_name"] = params["client_name"] # Client is the beneficiary in this scenario
        return params

    def generate_claim_retirement(self) -> dict:
        params = self._base_params("claim_retirement")
        params["main_type"] = "claims"
        params["retirement_date"] = (datetime.datetime.now() - datetime.timedelta(days=self.random.randint(0, 365))).strftime("%Y-%m-%d")
        return params

    def generate_random(self) -> dict:
        choices = [
            (self.generate_repurchase, 0.3),
            (self.generate_maintenance_client, 0.3),
            (self.generate_maintenance_contrib, 0.2),
            (self.generate_new_business, 0.1),
            (self.generate_claim_death, 0.05),
            (self.generate_claim_retirement, 0.05)
        ]
        funcs, weights = zip(*choices)
        func = self.random.choices(funcs, weights=weights, k=1)[0]
        return func()
