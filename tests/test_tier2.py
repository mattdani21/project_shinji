"""Tier 2: OCR & template matching for legacy (QR-less) forms."""
import os
import pytest

from generator.parameters import ParameterGenerator
from generator.forms.generic import GenericFormGenerator
from indexer.tiers.tier2 import Tier2TemplateMatcher, TEMPLATES


@pytest.fixture
def form_env(tmp_path):
    return {
        "param_gen": ParameterGenerator(seed=42),
        "form_gen": GenericFormGenerator(output_dir=str(tmp_path)),
        "out": str(tmp_path),
    }


def _params_for(form_env, sub_type, email_id="t2"):
    params = form_env["param_gen"].generate_random()
    # force the requested sub_type (generate_random may differ)
    params["sub_type"] = sub_type
    params["email_id"] = email_id
    return params


@pytest.mark.parametrize("sub_type", sorted(TEMPLATES.keys()))
def test_legacy_form_matches_its_template(form_env, sub_type):
    """Every legacy form type is routed correctly by its Form Ref marker."""
    params = _params_for(form_env, sub_type)
    pdf = form_env["form_gen"].generate(params, has_qr=False)
    res = Tier2TemplateMatcher().match_pdf(pdf)
    assert res is not None, f"no template match for {sub_type}"
    assert res["sub_type"] == sub_type
    assert res["tier"] == 2
    assert res["confidence"] >= 0.9  # form_ref hit -> 0.95
    assert res["status"] == "complete"
    assert res["signature_count"] >= 1


def test_incomplete_form_flagged_review(form_env):
    """Missing signature page -> incomplete status + capped confidence."""
    params = _params_for(form_env, "repurchase")
    pdf = form_env["form_gen"].generate(params, has_qr=False, include_signature=False)
    res = Tier2TemplateMatcher().match_pdf(pdf)
    assert res is not None
    assert res["sub_type"] == "repurchase"
    assert res["status"] == "incomplete"
    assert res["confidence"] <= 0.8
    assert "signature" in res["rfi_note"].lower()


def test_cover_letter_prepended_still_matches(form_env):
    """Broker cover letter as page 1 must not break template matching."""
    params = _params_for(form_env, "new_business")
    pdf = form_env["form_gen"].generate(params, has_qr=False, include_cover_letter=True)
    res = Tier2TemplateMatcher().match_pdf(pdf)
    assert res is not None
    assert res["sub_type"] == "new_business"
    assert res["page_count"] == 5  # cover letter + 3 content pages + signature page


def test_mixed_language_form_still_matches(form_env):
    """Afrikaans filler text must not break template matching."""
    params = _params_for(form_env, "claim_death")
    pdf = form_env["form_gen"].generate(params, has_qr=False, mixed_language=True)
    res = Tier2TemplateMatcher().match_pdf(pdf)
    assert res is not None
    assert res["sub_type"] == "claim_death"


def test_fields_extracted(form_env):
    """Policy number, ID and client name are extracted from the form text."""
    params = _params_for(form_env, "maintenance_contrib")
    pdf = form_env["form_gen"].generate(params, has_qr=False)
    res = Tier2TemplateMatcher().match_pdf(pdf)
    fields = res["extracted_fields"]
    assert fields.get("policy_number") == params["policy_number"]
    assert fields.get("id_number") == params["id_number"]
    assert params["client_name"].split()[0] in fields.get("client_name", "")


def test_no_match_returns_none():
    matcher = Tier2TemplateMatcher()
    assert matcher.match_text("completely unrelated shopping receipt text") is None
    # Weak field-label evidence below the acceptance threshold
    assert matcher.match_text("Policy Number: POL-12345678") is None


def test_title_only_match_above_threshold():
    matcher = Tier2TemplateMatcher(min_confidence=0.5)
    res = matcher.match_text("MERIDIAN WEALTH SOLUTIONS\nRepurchase / Withdrawal Form\nblah blah")
    assert res is not None
    assert res["sub_type"] == "repurchase"
    assert 0.5 <= res["confidence"] < 0.9


def test_engine_routes_legacy_form_via_tier2(form_env):
    """End-to-end: RuleEngine routes a QR-less form with method=tier2_template."""
    from indexer.rules.engine import RuleEngine
    params = _params_for(form_env, "claim_retirement", email_id="e2e_tier2")
    pdf = form_env["form_gen"].generate(params, has_qr=False)
    engine = RuleEngine()
    out = engine.process_inbound("e2e_tier2", "Legacy claim form attached.", pdf)
    assert out["type"] == "single"
    assert out["method"] == "tier2_template"
    task = out["tasks"][0]
    assert task["sub_type"] == "claim_retirement"
    assert task["status"] == "pending"  # 0.95 >= 0.85 -> auto-routed
    assert task["policy_number"] == params["policy_number"]
