"""
Adversarial Stress Test for Tessera AI Indexer.

Generates edge cases that WILL happen in reality to stress-test the model:
1. Legacy forms (no QR code)
2. Forms with broker cover letters (throws off page count)
3. Incomplete forms (missing signature = no boundary marker)
4. Mixed Afrikaans/English text
5. Bulk emails where each client has a different edge case
6. "Wrong form" — body says repurchase but attachment is maintenance
7. Body-only emails (no attachment at all)
"""
import os
import json
import random
import pandas as pd
from generator.parameters import ParameterGenerator
from generator.forms.generic import GenericFormGenerator
from generator.bodies.generate import BodyGenerator
from indexer.rules.engine import RuleEngine

class AdversarialTestGenerator:
    def __init__(self, output_dir: str = "data/adversarial_test"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.param_gen = ParameterGenerator(seed=555)
        self.form_gen = GenericFormGenerator(output_dir=self.output_dir)
        self.body_gen = BodyGenerator()
        self._rng = random.Random(555)
        
    def generate_all(self):
        """Generate all adversarial test cases."""
        manifest = []
        
        # ─── CATEGORY 1: Legacy forms (no QR code) ─────────────────
        # WILL happen: Many brokers still use old form templates
        print("Generating Category 1: Legacy forms (no QR)...")
        for i in range(20):
            params = self.param_gen.generate_random()
            params["email_id"] = "legacy_noqr_{}".format(i)
            body = self.body_gen.generate(params)
            
            body_path = os.path.join(self.output_dir, "{}_body.txt".format(params["email_id"]))
            with open(body_path, "w") as f:
                f.write(body)
                
            attachment = self.form_gen.generate(params, has_qr=False, rng=self._rng)
            
            manifest.append({
                "email_id": params["email_id"],
                "category": "legacy_no_qr",
                "ground_truth": params["sub_type"],
                "body_path": body_path,
                "attachment_path": attachment,
                "realistic": True,
                "expected_difficulty": "medium",
                "notes": "No QR code. Tier 1 fails. Must rely on Tier 4 (body + PDF text)."
            })
            
        # ─── CATEGORY 2: Cover letter prepended ────────────────────
        # WILL happen: Brokers always add a covering note as page 1
        print("Generating Category 2: Cover letter prepended...")
        for i in range(20):
            params = self.param_gen.generate_random()
            params["email_id"] = "cover_letter_{}".format(i)
            body = self.body_gen.generate(params)
            
            body_path = os.path.join(self.output_dir, "{}_body.txt".format(params["email_id"]))
            with open(body_path, "w") as f:
                f.write(body)
                
            attachment = self.form_gen.generate(
                params, has_qr=True, include_cover_letter=True, rng=self._rng
            )
            
            manifest.append({
                "email_id": params["email_id"],
                "category": "cover_letter",
                "ground_truth": params["sub_type"],
                "body_path": body_path,
                "attachment_path": attachment,
                "realistic": True,
                "expected_difficulty": "medium",
                "notes": "Cover letter as page 1 shifts all page numbers by 1."
            })

        # ─── CATEGORY 3: Incomplete form (no signature) ────────────
        # WILL happen: Clients forget to sign, broker sends anyway
        print("Generating Category 3: Incomplete forms (no signature)...")
        for i in range(20):
            params = self.param_gen.generate_random()
            params["email_id"] = "incomplete_{}".format(i)
            body = self.body_gen.generate(params)
            
            body_path = os.path.join(self.output_dir, "{}_body.txt".format(params["email_id"]))
            with open(body_path, "w") as f:
                f.write(body)
                
            attachment = self.form_gen.generate(
                params, has_qr=True, include_signature=False, rng=self._rng
            )
            
            manifest.append({
                "email_id": params["email_id"],
                "category": "incomplete_no_signature",
                "ground_truth": params["sub_type"],
                "body_path": body_path,
                "attachment_path": attachment,
                "realistic": True,
                "expected_difficulty": "hard",
                "notes": "No 'Declaration and Signature' page. Page splitter has NO boundary marker."
            })

        # ─── CATEGORY 4: Mixed Afrikaans/English ───────────────────
        # WILL happen: SA insurance world is bilingual
        print("Generating Category 4: Mixed Afrikaans/English...")
        for i in range(20):
            params = self.param_gen.generate_random()
            params["email_id"] = "afrikaans_mix_{}".format(i)
            
            # Afrikaans email body
            afrikaans_bodies = [
                "Goeiedag, ek wil graag my geld onttrek van polis {pol}. Sien asb aangeheg.",
                "Hiermee dien ek my eis in vir polis {pol}. Die vorms is aangeheg.",
                "Ek wil graag my adres verander op polis {pol}. Dankie.",
                "Ons klient wil graag sy premie verhoog op polis {pol}.",
            ]
            body = self._rng.choice(afrikaans_bodies).format(pol=params["policy_number"])
            
            body_path = os.path.join(self.output_dir, "{}_body.txt".format(params["email_id"]))
            with open(body_path, "w") as f:
                f.write(body)
                
            attachment = self.form_gen.generate(
                params, has_qr=True, mixed_language=True, rng=self._rng
            )
            
            manifest.append({
                "email_id": params["email_id"],
                "category": "afrikaans_mixed",
                "ground_truth": params["sub_type"],
                "body_path": body_path,
                "attachment_path": attachment,
                "realistic": True,
                "expected_difficulty": "hard",
                "notes": "Afrikaans body text. TF-IDF model was trained on English only."
            })

        # ─── CATEGORY 5: Wrong form mismatch ──────────────────────
        # WILL happen: Body says "withdrawal" but attachment is maintenance
        print("Generating Category 5: Body/attachment mismatch...")
        for i in range(10):
            # Generate body for one type
            body_params = self.param_gen.generate_repurchase()
            body_params["email_id"] = "mismatch_{}".format(i)
            body = self.body_gen.generate(body_params)
            
            # Generate attachment for a DIFFERENT type
            attach_params = self.param_gen.generate_maintenance_client()
            attach_params["email_id"] = "mismatch_{}".format(i)
            
            body_path = os.path.join(self.output_dir, "{}_body.txt".format(body_params["email_id"]))
            with open(body_path, "w") as f:
                f.write(body)
                
            attachment = self.form_gen.generate(attach_params, has_qr=True, rng=self._rng)
            
            manifest.append({
                "email_id": body_params["email_id"],
                "category": "body_attachment_mismatch",
                "ground_truth": attach_params["sub_type"],  # Attachment is truth
                "body_path": body_path,
                "attachment_path": attachment,
                "realistic": True,
                "expected_difficulty": "hard",
                "notes": "Body says repurchase, attachment is maintenance. Attachment should win."
            })

        # ─── CATEGORY 6: Body-only (no attachment) ─────────────────
        # WILL happen: Client sends email asking for help, no form attached
        print("Generating Category 6: Body-only (no attachment)...")
        for i in range(10):
            params = self.param_gen.generate_random()
            params["email_id"] = "bodyonly_{}".format(i)
            body = self.body_gen.generate(params)
            
            body_path = os.path.join(self.output_dir, "{}_body.txt".format(params["email_id"]))
            with open(body_path, "w") as f:
                f.write(body)
                
            manifest.append({
                "email_id": params["email_id"],
                "category": "body_only",
                "ground_truth": params["sub_type"],
                "body_path": body_path,
                "attachment_path": None,
                "realistic": True,
                "expected_difficulty": "easy",
                "notes": "No attachment. Classification from body text only."
            })

        # Save manifest
        df = pd.DataFrame(manifest)
        manifest_path = os.path.join(self.output_dir, "adversarial_manifest.csv")
        df.to_csv(manifest_path, index=False)
        print("\nAdversarial test set generated: {} cases".format(len(manifest)))
        print("Manifest saved to: {}".format(manifest_path))
        return manifest


def run_adversarial_eval(test_dir: str = "data/adversarial_test"):
    """Run the full indexer pipeline against the adversarial test set."""
    from indexer.workqueue import WorkQueueManager
    import shutil
    
    # Clean work queues for a fresh test
    wq_dir = "data/workqueues"
    if os.path.exists(wq_dir):
        shutil.rmtree(wq_dir)
    
    engine = RuleEngine()
    df = pd.read_csv(os.path.join(test_dir, "adversarial_manifest.csv"))
    
    results = []
    
    for _, row in df.iterrows():
        body = open(row["body_path"]).read()
        attachment = row["attachment_path"] if pd.notna(row["attachment_path"]) else None
        
        out = engine.process_inbound(row["email_id"], body, attachment)
        
        # Get the primary prediction
        if out["type"] == "error":
            prediction = "error"
            confidence = 0.0
        elif out.get("tasks"):
            # Take the first task's prediction
            prediction = out["tasks"][0].get("sub_type", "unknown")
            confidence = out["tasks"][0].get("confidence", 0.0)
        else:
            prediction = "unknown"
            confidence = 0.0
            
        is_correct = prediction == row["ground_truth"]
        
        results.append({
            "email_id": row["email_id"],
            "category": row["category"],
            "ground_truth": row["ground_truth"],
            "prediction": prediction,
            "confidence": confidence,
            "is_correct": is_correct,
            "notes": row["notes"]
        })
        
    res_df = pd.DataFrame(results)
    
    # Print results by category
    print("\n" + "=" * 70)
    print("ADVERSARIAL TEST RESULTS")
    print("=" * 70)
    
    for cat in res_df["category"].unique():
        cat_df = res_df[res_df["category"] == cat]
        acc = cat_df["is_correct"].mean()
        avg_conf = cat_df["confidence"].mean()
        count = len(cat_df)
        print("\n{} ({} samples)".format(cat.upper(), count))
        print("  Accuracy:   {:.1%}".format(acc))
        print("  Avg Conf:   {:.1%}".format(avg_conf))
        
        # Show failures
        failures = cat_df[~cat_df["is_correct"]]
        if not failures.empty:
            print("  FAILURES:")
            for _, fail in failures.head(3).iterrows():
                print("    {} -> predicted '{}' (truth: '{}', conf: {:.1%})".format(
                    fail["email_id"], fail["prediction"], fail["ground_truth"], fail["confidence"]
                ))
    
    overall = res_df["is_correct"].mean()
    print("\n" + "-" * 70)
    print("OVERALL ACCURACY: {:.1%} ({}/{})".format(overall, res_df["is_correct"].sum(), len(res_df)))
    print("-" * 70)
    
    # Save results
    res_df.to_csv(os.path.join(test_dir, "adversarial_results.csv"), index=False)
    return res_df


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        run_adversarial_eval()
    else:
        gen = AdversarialTestGenerator()
        gen.generate_all()
        print("\nNow run:  PYTHONPATH=. python generator/adversarial_test.py eval")
