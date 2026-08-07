"""Tessera AI Indexer — end-to-end mini demo.

Runs 8 representative inbound emails through the REAL pipeline
(RuleEngine.process_inbound — the same path batch ingest / watcher use)
and prints a decision table covering every tier + the HITL paths:

  1. clean_qr        modern form with QR            -> Tier 1, auto-route
  2. cover_letter    QR form + broker cover page    -> Tier 1 (page offset)
  3. incomplete      QR form, missing signature     -> Tier 1 -> HITL (RFI)
  4. legacy_nqr      old form, no QR                -> Tier 2 template match
  5. afrikaans       mixed-language email + form    -> Tier 1 (QR wins)
  6. body_only       no attachment, keyword body    -> Tier 3 NER
  7. unreadable      blank/scanned attachment       -> review + RFI (no silent drop)
  8. messy_typos     typo-riddled body + QR form    -> Tier 1

Usage:
    PYTHONPATH=. python demo/mini_demo.py
    PYTHONPATH=. python demo/mini_demo.py --keep    # keep demo/run/ artifacts

Artifacts (deleted unless --keep):
    demo/run/workqueues/*.jsonl      routed team queues
    demo/run/human_review/           HITL exports + review manifest
"""
import argparse
import os
import shutil
import sys

RUN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run")


def _make_case(generators, sub_type, email_id, **overrides):
    params = generators["params"].generate_random()
    params["sub_type"] = sub_type
    params["email_id"] = email_id
    params.update(overrides)
    return params


def build_cases(generators, out_dir):
    form = generators["form"]
    bodies = generators["bodies"]
    rng = generators["rng"]
    cases = []

    # 1. Clean QR form
    p = _make_case(generators, "repurchase", "clean_qr")
    body = bodies.generate(p)
    pdf = form.generate(p, has_qr=True)
    cases.append(("clean_qr", "repurchase", "modern QR form + clean body", body, pdf))

    # 2. Cover letter prepended
    p = _make_case(generators, "new_business", "cover_letter")
    body = bodies.generate(p)
    pdf = form.generate(p, has_qr=True, include_cover_letter=True)
    cases.append(("cover_letter", "new_business", "QR form + broker cover page", body, pdf))

    # 3. Incomplete form (signature page missing)
    p = _make_case(generators, "repurchase", "incomplete")
    body = bodies.generate(p)
    pdf = form.generate(p, has_qr=True, include_signature=False)
    cases.append(("incomplete", "repurchase", "QR form, signature page missing", body, pdf))

    # 4. Legacy form (no QR) -> Tier 2
    p = _make_case(generators, "claim_retirement", "legacy_nqr")
    body = bodies.generate(p)
    pdf = form.generate(p, has_qr=False)
    cases.append(("legacy_nqr", "claim_retirement", "legacy form, no QR", body, pdf))

    # 5. Afrikaans body + QR form
    p = _make_case(generators, "maintenance_client", "afrikaans")
    body = "Goeiedag, ek wil graag my adres verander op polis {pol}. Sien asb aangeheg.".format(
        pol=p["policy_number"])
    pdf = form.generate(p, has_qr=True, mixed_language=True)
    cases.append(("afrikaans", "maintenance_client", "Afrikaans body + QR form", body, pdf))

    # 6. Body-only (no attachment) -> Tier 3
    p = _make_case(generators, "maintenance_contrib", "body_only")
    body = bodies.generate(p)
    cases.append(("body_only", "maintenance_contrib", "no attachment, keyword-rich body", body, None))

    # 7. Unreadable attachment (blank PDF) -> HITL with RFI
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    p = _make_case(generators, "repurchase", "unreadable")
    blank = os.path.join(out_dir, "unreadable_blank.pdf")
    c = canvas.Canvas(blank, pagesize=A4)
    c.showPage()
    c.save()
    body = ("Good day,\n\nI would like to request a partial withdrawal from my "
            "policy {pol}. The signed form is attached.\n\nRegards,\nJane Doe").format(pol=p["policy_number"])
    cases.append(("unreadable", "repurchase", "blank PDF attachment", body, blank))

    # 8. Messy typo body + QR form
    p = _make_case(generators, "claim_death", "messy_typos")
    body = bodies.generate(p, messy=True)
    pdf = form.generate(p, has_qr=True)
    cases.append(("messy_typos", "claim_death", "typo-riddled body + QR form", body, pdf))

    return cases


def run():
    parser = argparse.ArgumentParser(description="Tessera AI Indexer mini demo")
    parser.add_argument("--keep", action="store_true", help="keep demo/run/ artifacts")
    args = parser.parse_args()

    if os.path.exists(RUN_DIR):
        shutil.rmtree(RUN_DIR)
    os.makedirs(RUN_DIR)

    # Local imports so the demo works from a source checkout
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from generator.parameters import ParameterGenerator
    from generator.forms.generic import GenericFormGenerator
    from generator.bodies.generate import BodyGenerator
    from indexer.rules.engine import RuleEngine
    import random

    generators = {
        "params": ParameterGenerator(seed=42),
        "form": GenericFormGenerator(output_dir=RUN_DIR),
        "bodies": BodyGenerator(),
        "rng": random.Random(42),
    }

    # Isolate runtime dirs from the repo
    engine = RuleEngine()

    # Point work queues + review at the demo run dir
    engine.config.queue_dir = os.path.join(RUN_DIR, "workqueues")
    engine.config.review_dir = os.path.join(RUN_DIR, "human_review")
    engine.config.hitl_threshold = 0.85

    print("=" * 78)
    print("TESSERA AI INDEXER — END-TO-END MINI DEMO")
    print("=" * 78)
    print(f"{'case':<14}{'route':<30}{'prediction':<20}{'conf':<7}{'status':<9}{'queue'}")
    print("-" * 78)

    review_items = []
    cases = build_cases(generators, RUN_DIR)
    for email_id, truth, note, body, pdf in cases:
        out = engine.process_inbound(email_id, body, pdf)
        if out["type"] == "error":
            print(f"{email_id:<14}{'ERROR':<30}{out.get('message', '')[:60]}")
            continue
        method = out.get("method", "body_only_classify")
        tasks = out.get("tasks") or []
        if tasks:
            t = tasks[0]
            pred, conf, status = t["sub_type"], t["confidence"], t["status"]
            queue = t.get("routed_to") or out.get("routed_to") or "-"
            mark = "OK " if pred == truth else "!! "
            if status == "review":
                rfi = (t.get("extracted_fields") or {}).get("rfi_reason") or "low confidence"
                review_items.append((email_id, conf, rfi))
        else:
            pred, conf, status, queue = "-", 0.0, "-", "-"
            mark = "?? "
        print(f"{mark}{email_id:<12}{method:<30}{pred:<20}{conf:<7.0%}{status:<9}{queue}")

    print("-" * 78)
    print("Legend: OK = prediction matches ground truth · !! = mismatch")
    print()
    print("What to look at next:")
    print(f"  Team queues:     {engine.config.queue_dir}/")
    print(f"  HITL review:     {engine.config.review_dir}/")
    print()
    for f in sorted(os.listdir(engine.config.queue_dir)):
        path = os.path.join(engine.config.queue_dir, f)
        n = sum(1 for _ in open(path))
        print(f"  {f}: {n} item(s)")
    if review_items:
        print()
        print("Items routed to human review (with reason):")
        for email_id, conf, rfi in review_items:
            print(f"  - {email_id:<14} conf {conf:.0%}  {rfi}")

    if not args.keep:
        shutil.rmtree(RUN_DIR)
        print("\n(demo artifacts cleaned — rerun with --keep to inspect them)")
    print("\nDemo complete.")


if __name__ == "__main__":
    run()
