import pytest
from pathlib import Path
from indexer.rules.engine import RuleEngine

@pytest.fixture
def rule_engine():
    # Use paths relative to project root
    return RuleEngine(
        taxonomy_path="taxonomy/taxonomy.yaml",
        schema_dir="taxonomy/schemas"
    )

def test_engine_initialization(rule_engine):
    assert len(rule_engine.schemas) == 6
    assert "repurchase" in rule_engine.schemas
    assert "new_business" in rule_engine.schemas

def test_validate_valid_repurchase(rule_engine):
    data = {
        "policy_number": "POL-12345678",
        "id_number": "9001015000000",
        "client_name": "John Doe",
        "repurchase_amount": 1500.50,
        "is_full_withdrawal": False
    }
    result = rule_engine.validate_extracted_data("repurchase", data)
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
    assert result["validated_data"]["client_name"] == "John Doe"

def test_validate_invalid_pattern(rule_engine):
    data = {
        "policy_number": "INVALID_POL",
        "id_number": "9001015000000",
        "client_name": "John Doe",
        "is_full_withdrawal": True
    }
    result = rule_engine.validate_extracted_data("repurchase", data)
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert any("policy_number" in err for err in result["errors"])

def test_validate_missing_required_field(rule_engine):
    data = {
        "policy_number": "POL-12345678",
        # missing id_number
        "client_name": "John Doe",
        "is_full_withdrawal": True
    }
    result = rule_engine.validate_extracted_data("repurchase", data)
    assert result["is_valid"] is False
    assert any("id_number" in err for err in result["errors"])

def test_validate_unknown_schema(rule_engine):
    result = rule_engine.validate_extracted_data("unknown", {})
    assert result["is_valid"] is False
    assert "Schema 'unknown' not found" in result["errors"][0]
