import os
import random
import json
import pandas as pd
from generator.parameters import ParameterGenerator
from generator.forms.generic import GenericFormGenerator
from generator.bodies.generate import BodyGenerator

class MessyCorpusGenerator:
    def __init__(self, output_dir: str = "data/stress_test"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.param_gen = ParameterGenerator(seed=777)
        self.form_gen = GenericFormGenerator(output_dir=self.output_dir)
        self.body_gen = BodyGenerator()
        self._rng = random.Random(777)

    def generate_stress_corpus(self, num_samples: int = 500):
        print(f"Generating {num_samples} messy/ambiguous samples...")
        manifest = []
        
        for i in range(num_samples):
            # Decide what kind of messy sample to make
            mode = self._rng.choice(["typos", "ambiguous", "vague", "irrelevant",
                                     "legacy_form", "keyword_body"])
            
            params = self.param_gen.generate_random()
            email_id = f"stress_{i}_{mode}"
            params['email_id'] = email_id
            
            if mode == "typos":
                body = self.body_gen.generate(params, messy=True)
                ground_truth = params["sub_type"]
            elif mode == "ambiguous":
                body = self.body_gen._generate_ambiguous()
                ground_truth = "ambiguous"
            elif mode == "vague":
                body = "Hi, I need help with my insurance. Please call me back. I am not sure what form to use."
                ground_truth = "unknown"
            elif mode == "irrelevant":
                body = "Wrong number, sorry. I was trying to reach my doctor."
                ground_truth = "irrelevant"
            elif mode == "legacy_form":
                # Tier 2 stress: legacy form (no QR) with a noisy/typo body
                body = self.body_gen.generate(params, messy=True)
                ground_truth = params["sub_type"]
                params['sub_type'] = params["sub_type"]
            else:  # keyword_body
                # Tier 3 stress: body-only with keyword evidence but no attachment
                body = self.body_gen.generate(params)
                ground_truth = params["sub_type"]

            # Save body
            body_path = os.path.join(self.output_dir, f"{email_id}_body.txt")
            with open(body_path, "w") as f:
                f.write(body)
                
            attachment_path = None
            if mode == "legacy_form":
                # QR-less form attachment — Tier 2 must route it
                attachment_path = self.form_gen.generate(
                    params, has_qr=False, mixed_language=(i % 3 == 0), rng=self._rng
                )
                
            manifest.append({
                "email_id": email_id,
                "mode": mode,
                "ground_truth": ground_truth,
                "body_path": body_path,
                "attachment_path": attachment_path
            })
            
        df = pd.DataFrame(manifest)
        df.to_csv(os.path.join(self.output_dir, "stress_manifest.csv"), index=False)
        print(f"Stress corpus generated in {self.output_dir}")

if __name__ == "__main__":
    gen = MessyCorpusGenerator()
    gen.generate_stress_corpus(500)
