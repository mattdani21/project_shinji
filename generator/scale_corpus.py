import os
import json
import random
import pandas as pd
import concurrent.futures
from generator.parameters import ParameterGenerator
from generator.forms.generic import GenericFormGenerator
from generator.bodies.generate import BodyGenerator
from generator.broker_generator import BrokerGenerator

def generate_single_sample(args):
    sub_type, i, output_dir, seed = args
    
    # Each worker needs its own generators to be thread/process safe
    param_gen = ParameterGenerator(seed=seed + i)
    form_gen = GenericFormGenerator(output_dir=output_dir)
    body_gen = BodyGenerator()
    broker_gen = BrokerGenerator(output_dir=output_dir)
    rng = random.Random(seed + i)
    
    email_id = f"{sub_type}_{i}"
    params = getattr(param_gen, f"generate_{sub_type}")()
    params["email_id"] = email_id
    
    # Diversity sampling
    dice = rng.random()
    diversity = "clean"
    if dice < 0.10: diversity = "legacy"
    elif dice < 0.20: diversity = "afrikaans"
    elif dice < 0.25: diversity = "cover_letter"
    elif dice < 0.30: diversity = "broker_bulk"
    
    if diversity == "broker_bulk":
        res = broker_gen.generate_bulk_instruction(f"bulk_{i}", num_clients=rng.randint(2, 4))
        return {
            "email_id": res["email_id"],
            "investor_id": "BROKER",
            "main_type": "broker_comms",
            "sub_type": "bulk_instructions",
            "pdf_path": res["attachment_path"],
            "body_path": res["body_path"],
            "diversity": "broker_bulk",
            "ground_truth_count": len(res["clients"])
        }
    else:
        has_qr = diversity != "legacy"
        include_cover_letter = diversity == "cover_letter"
        mixed_language = diversity == "afrikaans"
        
        if mixed_language:
            afrikaans_bodies = [
                "Goeiedag, ek wil graag my geld onttrek van polis {pol}. Sien asb aangeheg.",
                "Hiermee dien ek my eis in vir polis {pol}. Die vorms is aangeheg.",
                "Ek wil graag my adres verander op polis {pol}. Dankie.",
                "Ons klient wil graag sy premie verhoog op polis {pol}.",
                "Ek tree af op my aftree-datum en wil graag my voordele eis vir polis {pol}.",
                "Hiermee die voltooide vorm vir polis {pol}. Verwerk asseblief.",
            ]
            body_text = rng.choice(afrikaans_bodies).format(pol=params["policy_number"])
        else:
            body_text = body_gen.generate(params)
        
        body_path = os.path.join(output_dir, f"{email_id}_body.txt")
        with open(body_path, "w") as f: f.write(body_text)
        
        pdf_path = form_gen.generate(
            params, has_qr=has_qr, include_cover_letter=include_cover_letter, 
            mixed_language=mixed_language, rng=rng
        )
        
        return {
            "email_id": email_id, "investor_id": params["investor_id"],
            "main_type": params["main_type"], "sub_type": params["sub_type"],
            "pdf_path": pdf_path, "body_path": body_path,
            "diversity": diversity, "ground_truth_count": 1
        }

def generate_scaled_corpus(total_emails: int = 10000, output_dir: str = "data/corpus_10k", checkpoint_interval: int = 500):
    print(f"Scaling corpus to {total_emails} samples using parallel processing...")
    os.makedirs(output_dir, exist_ok=True)
    
    seed = 777
    dist = {
        "repurchase": 0.30,
        "maintenance_client": 0.25,
        "maintenance_contrib": 0.15,
        "new_business": 0.15,
        "claim_death": 0.075,
        "claim_retirement": 0.075
    }
    
    counts = {k: int(v * total_emails) for k, v in dist.items()}
    current_total = sum(counts.values())
    if current_total < total_emails:
        counts["repurchase"] += (total_emails - current_total)
        
    tasks = []
    global_idx = 0
    for sub_type, count in counts.items():
        for i in range(count):
            tasks.append((sub_type, global_idx, output_dir, seed))
            global_idx += 1
            
    manifest_data = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(generate_single_sample, task): task for task in tasks}
        
        count = 0
        for future in concurrent.futures.as_completed(futures):
            manifest_data.append(future.result())
            count += 1
            if count % checkpoint_interval == 0:
                print(f"  Generated {count}/{total_emails}... Saving checkpoint.")
                pd.DataFrame(manifest_data).to_parquet(os.path.join(output_dir, "manifest_10k.parquet"), index=False)

    df = pd.DataFrame(manifest_data)
    df.to_parquet(os.path.join(output_dir, "manifest_10k.parquet"), index=False)
    
    print(f"\n=== Corpus Generation Complete ===")
    print(f"Total samples: {len(df)}")
    print(f"\nDistribution:")
    for sub, cnt in df["sub_type"].value_counts().items():
        print(f"  {sub}: {cnt} ({cnt/len(df)*100:.1f}%)")
    print(f"\nDiversity:")
    for div, cnt in df["diversity"].value_counts().items():
        print(f"  {div}: {cnt} ({cnt/len(df)*100:.1f}%)")
    print(f"Manifest saved to {output_dir}/manifest_10k.parquet")

if __name__ == "__main__":
    generate_scaled_corpus(10000)
