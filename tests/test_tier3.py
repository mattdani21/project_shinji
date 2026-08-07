"""Tier 3: NER & keyword/taxonomy classification over unstructured text."""
import pytest

from generator.parameters import ParameterGenerator
from generator.bodies.generate import BodyGenerator
from indexer.tiers.tier3 import Tier3NERExtractor, KEYWORDS
from indexer.rules.engine import RuleEngine


@pytest.fixture
def ner():
    return Tier3NERExtractor()


def _body_for(sub_type):
    params = ParameterGenerator(seed=7).generate_random()
    params["sub_type"] = sub_type
    params["email_id"] = "t3"
    return params, BodyGenerator().generate(params)


@pytest.mark.parametrize("sub_type", sorted(KEYWORDS.keys()))
def test_body_classifies_to_its_own_type(ner, sub_type):
    """Generated bodies for every sub_type route via tier3 NER."""
    params, body = _body_for(sub_type)
    res = ner.classify(body)
    assert res is not None, f"no tier3 evidence for {sub_type} body: {body[:120]}"
    assert res["prediction"] == sub_type, f"{sub_type} body misclassified: {res['evidence']}"
    assert res["tier"] == 3
    assert res["confidence"] >= ner.min_confidence


def test_unknown_text_returns_none(ner):
    assert ner.classify("The weather is nice today. Please call me back about the garden.") is None
    assert ner.classify("") is None


def test_ambiguous_text_low_confidence_or_none(ner):
    # Contains signals for two types at once
    text = ("I moved to a new house and also want to withdraw all my money "
            "from my policy POL-12345678. Attached are both forms.")
    res = ner.classify(text)
    if res is not None:
        # Either low confidence (below auto-route threshold) or none at all
        assert res["confidence"] < 0.85


def test_afrikaans_withdrawal_body(ner):
    params = ParameterGenerator(seed=8).generate_repurchase()
    body = "Goeiedag, ek wil graag my geld onttrek van polis {}. Sien asb aangeheg.".format(
        params["policy_number"]
    )
    res = ner.classify(body)
    assert res is not None
    assert res["prediction"] == "repurchase"


def test_afrikaans_claim_body_ambiguous_but_claim(ner):
    body = "Hiermee dien ek my eis in vir polis POL-12345678. Die vorms is aangeheg."
    res = ner.classify(body)
    if res is not None:
        assert res["prediction"] in ("claim_death", "claim_retirement")


def test_extract_policy_and_name(ner):
    body = ("Good day,\n\nI would like to request a partial withdrawal from my "
            "policy POL-88888888. The signed form is attached.\n\nRegards,\nThabo Mokoena")
    fields = ner.extract(body)
    assert fields.get("policy_number") == "POL-88888888"
    assert fields.get("client_name") == "Thabo Mokoena"


def test_engine_classifies_body_only_email_via_tier3(ner):
    params, body = _body_for("claim_death")
    engine = RuleEngine()
    out = engine.classify_email(body)
    assert out["tier"] == 3
    assert out["prediction"] == "claim_death"
    assert out["method"] == "local_ner_keyword"


def test_engine_process_inbound_body_only_routes_via_tier3():
    params, body = _body_for("maintenance_contrib")
    engine = RuleEngine()
    out = engine.process_inbound("t3_e2e", body, None)
    assert out["type"] == "single"
    task = out["tasks"][0]
    assert task["sub_type"] == "maintenance_contrib"
    assert task["confidence"] >= 0.5
    assert task["extracted_fields"].get("policy_number") == params["policy_number"]


def test_confidences_are_well_calibrated(ner):
    """Strong multi-signal bodies score high; single-signal bodies score lower."""
    strong = ("I am writing to submit a death claim under policy POL-12345678. "
              "The policyholder has passed away. The death certificate number is DC-001.")
    weak = "I would like to claim my retirement benefits."
    strong_res = ner.classify(strong)
    weak_res = ner.classify(weak)
    assert strong_res is not None and weak_res is not None
    assert strong_res["prediction"] == "claim_death"
    assert strong_res["confidence"] > weak_res["confidence"]
