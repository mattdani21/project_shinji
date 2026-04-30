import yaml
from pathlib import Path
from pydantic import BaseModel, create_model, Field
from typing import Any, Dict, List, Optional
import re
from indexer.tiers.tier4 import Tier4Classifier

class SchemaField(BaseModel):
    name: str
    type: str
    required: bool
    pattern: Optional[str] = None

class FormSchema(BaseModel):
    schema_id: str
    name: str
    description: str
    fields: List[SchemaField]

class RuleEngine:
    def __init__(self, taxonomy_path: str = "taxonomy/taxonomy.yaml", schema_dir: str = "taxonomy/schemas"):
        self.taxonomy_path = Path(taxonomy_path)
        self.schema_dir = Path(schema_dir)
        self.taxonomy = self._load_yaml(self.taxonomy_path)
        self.schemas: Dict[str, FormSchema] = {}
        self.pydantic_models: Dict[str, Any] = {}
        self._load_schemas()
        
        # Initialize Tier 4 Classifier (On-Prem ML)
        try:
            self.tier4 = Tier4Classifier()
            print("Tier 4 Classifier initialized successfully.")
        except Exception as e:
            print(f"Tier 4 initialization failed: {e}. Fallback to basic keyword matching might be needed.")
            self.tier4 = None

    def _load_yaml(self, path: Path) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _load_schemas(self):
        for sub_type in self.taxonomy.get('sub_types', []):
            schema_file = sub_type.get('schema_file')
            if not schema_file:
                continue
            
            schema_path = self.schema_dir / schema_file
            if schema_path.exists():
                schema_data = self._load_yaml(schema_path)
                form_schema = FormSchema(**schema_data)
                self.schemas[form_schema.schema_id] = form_schema
                self.pydantic_models[form_schema.schema_id] = self._create_pydantic_model(form_schema)

    def _create_pydantic_model(self, form_schema: FormSchema) -> Any:
        fields = {}
        for field in form_schema.fields:
            # Map simple types to python types
            type_mapping = {
                'string': str,
                'float': float,
                'boolean': bool,
                'integer': int
            }
            py_type = type_mapping.get(field.type, str)
            
            # Add regex pattern validation if present
            field_args = {}
            if field.pattern:
                field_args['pattern'] = field.pattern
                
            if field.required:
                fields[field.name] = (py_type, Field(..., **field_args))
            else:
                fields[field.name] = (Optional[py_type], Field(default=None, **field_args))
                
        return create_model(f"{form_schema.schema_id.capitalize()}Model", **fields)

    def validate_extracted_data(self, schema_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the extracted data against the specified schema.
        Returns a dictionary with 'is_valid', 'validated_data', and 'errors'.
        """
        if schema_id not in self.pydantic_models:
            return {
                "is_valid": False,
                "errors": [f"Schema '{schema_id}' not found."],
                "validated_data": None
            }

        model = self.pydantic_models[schema_id]
        
        try:
            validated = model(**data)
            return {
                "is_valid": True,
                "errors": [],
                "validated_data": validated.model_dump()
            }
        except Exception as e:
            # Parse pydantic validation errors
            from pydantic import ValidationError
            errors = []
            if isinstance(e, ValidationError):
                for error in e.errors():
                    loc = ".".join(str(x) for x in error["loc"])
                    msg = error["msg"]
                    errors.append(f"{loc}: {msg}")
            else:
                errors.append(str(e))
                
            return {
                "is_valid": False,
                "errors": errors,
                "validated_data": None
            }

    def classify_email(self, body_text: str, attachments: List[str] = []) -> Dict[str, Any]:
        """
        Implements the 4-tier classification system:
        Tier 1: Deterministic QR (Simulated)
        Tier 2-3: Regex/Validation (Handled by RuleEngine)
        Tier 4: Local ML (Fallback)
        """
        # Tier 1: Check for simulated QR code in attachments
        # (In our synthetic corpus, we can look for strings in filenames or just metadata)
        for attachment in attachments:
            if "qr_type:" in attachment:
                schema_id = attachment.split("qr_type:")[1].split(".")[0]
                return {
                    "tier": 1,
                    "prediction": schema_id,
                    "confidence": 1.0,
                    "method": "deterministic_qr"
                }

        # Tier 2-3: Handled by validation if data is already extracted
        # (For this flow, we assume we're classifying raw body text)

        # Tier 4: Local ML Fallback
        if self.tier4:
            result = self.tier4.predict(body_text)
            return {
                "tier": 4,
                "prediction": result["prediction"],
                "confidence": result["confidence"],
                "latency_ms": result["latency_ms"],
                "method": "local_ml_fallback"
            }

        return {
            "tier": 0,
            "prediction": "unknown",
            "confidence": 0.0,
            "method": "none"
        }
