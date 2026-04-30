import os
import json
import time
import pandas as pd
from generator.parameters import ParameterGenerator
from generator.forms.generic import GenericFormGenerator
from generator.bodies.generate import BodyGenerator

def generate_vertical_slice(num_emails: int = 3000, batch_size: int = 100):
    print(f"Generating {num_emails} synthetic emails across all forms...")
    print(f"  Using batches of {batch_size} with saves between batches")
    
    # 1. Initialize generators
    param_gen = ParameterGenerator(seed=42)
    form_gen = GenericFormGenerator(output_dir="data/corpus")
    body_gen = BodyGenerator(delay_seconds=2.0)
    
    manifest_data = []
    log_data = []
    
    cost_per_email = 0.05 # Gemini Flash estimate
    api_success_count = 0
    mock_count = 0
    
    for i in range(num_emails):
        # 2. Sample parameters
        params = param_gen.generate_random()
        email_id = params['email_id']
        
        if (i + 1) % 50 == 0 or i == 0:
            print(f"[{i+1}/{num_emails}] Generating {params['sub_type']} email...")
        
        # 3. Generate Form PDF
        pdf_path = form_gen.generate(params)
        
        # 4. Generate Body
        body_text = body_gen.generate(params)
        
        # Track API vs mock usage
        if "attached" in body_text.lower() and len(body_text) > 100:
            api_success_count += 1
        else:
            mock_count += 1
        
        # Save body text to file
        body_path = f"data/corpus/{email_id}_body.txt"
        with open(body_path, "w") as f:
            f.write(body_text)
            
        # 5. Build manifest entry (ground truth)
        manifest_entry = {
            "email_id": email_id,
            "main_type": params["main_type"],
            "sub_type": params["sub_type"],
            "pdf_path": pdf_path,
            "body_path": body_path,
            "ground_truth": params
        }
        manifest_data.append(manifest_entry)
        
        # 6. Audit Logging
        log_entry = {
            "email_id": email_id,
            "prompt_params": params,
            "generated_body": body_text,
            "api_used": "gemini-flash-latest" if body_gen.api_key else "mocked",
            "cost_zar": cost_per_email if body_gen.api_key else 0.0
        }
        log_data.append(log_entry)
        
        # Batch save every batch_size emails
        if (i + 1) % batch_size == 0:
            _save_checkpoint(manifest_data, log_data, i + 1, num_emails)
    
    # Final save
    _save_checkpoint(manifest_data, log_data, num_emails, num_emails)
    
    total_cost = sum([l["cost_zar"] for l in log_data])
    print(f"\nGeneration complete!")
    print(f"  API successes: {api_success_count}")
    print(f"  Mock fallbacks: {mock_count}")
    print(f"  Total simulated API cost: R {total_cost:.2f}")

def _save_checkpoint(manifest_data, log_data, current, total):
    df = pd.DataFrame(manifest_data)
    df.to_parquet("data/manifest.parquet", index=False)
    
    with open("data/generation_audit.jsonl", "w") as f:
        for entry in log_data:
            f.write(json.dumps(entry) + "\n")
    
    print(f"  Checkpoint saved ({current}/{total})")

if __name__ == "__main__":
    import sys
    count = 3000
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    generate_vertical_slice(count)
