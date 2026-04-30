import os
import json
import pandas as pd
from generator.parameters import ParameterGenerator
from generator.forms.generic import GenericFormGenerator
from generator.bodies.generate import BodyGenerator
from indexer.rules.engine import RuleEngine

def run_stress_test(num_samples: int = 500):
    print(f"Running Stress Test with {num_samples} messy emails...")
    
    param_gen = ParameterGenerator(seed=999)
    form_gen = GenericFormGenerator(output_dir="data/stress_corpus")
    body_gen = BodyGenerator()
    engine = RuleEngine()
    
    results = []
    
    # 1. Messy samples
    for i in range(num_samples):
        params = param_gen.generate_random()
        email_id = f"messy_{i}"
        params['email_id'] = email_id
        body_text = body_gen.generate(params, messy=True)
        out = engine.classify_email(body_text)
        results.append({
            "email_id": email_id,
            "ground_truth": params["sub_type"],
            "prediction": out["prediction"],
            "confidence": out["confidence"],
            "is_correct": out["prediction"] == params["sub_type"],
            "body": body_text[:100] + "..."
        })

    # 2. Truly Ambiguous (Mixed) samples
    print(f"Adding 50 ambiguous mixed-signal emails...")
    for i in range(50):
        email_id = f"ambiguous_{i}"
        body_text = body_gen._generate_ambiguous() # This mixes types
        out = engine.classify_email(body_text)
        results.append({
            "email_id": email_id,
            "ground_truth": "ambiguous",
            "prediction": out["prediction"],
            "confidence": out["confidence"],
            "is_correct": False, # Cannot be truly correct if ambiguous
            "body": body_text[:100] + "..."
        })
        
    res_df = pd.DataFrame(results)
    accuracy = res_df["is_correct"].mean()
    avg_conf = res_df["confidence"].mean()
    
    print(f"\nStress Test Results:")
    print(f"  Accuracy: {accuracy:.2%}")
    print(f"  Avg Confidence: {avg_conf:.2%}")
    
    # Show examples where it struggled (confidence < 0.9)
    struggled = res_df[res_df["confidence"] < 0.9]
    if not struggled.empty:
        print(f"\nSamples with low confidence (<90%):")
        print(struggled[["ground_truth", "prediction", "confidence", "body"]].head(5))
    else:
        print("\nSurprisingly, the model still has high confidence in all messy samples!")

if __name__ == "__main__":
    run_stress_test()
