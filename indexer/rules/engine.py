import os
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

    def process_inbound(self, email_id: str, body_text: str, attachment_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point for the indexing pipeline.
        
        This is what the human indexer does today:
        1. Opens the email
        2. Opens the PDF attachment
        3. Reads through the pages
        4. Identifies each form boundary (end of one client's application)
        5. For each form: extracts the policy number, identifies the form type
        6. Routes each form as a task to the correct team work queue
        
        Supports both single-client and broker bulk (1:N) emails.
        """
        import pypdf
        from indexer.workqueue import (
            WorkQueueItem, WorkQueueManager, 
            extract_policy_number, extract_client_name
        )
        
        wq = WorkQueueManager()
        
        # --- If no attachment, classify from body text only ---
        if not attachment_path or not os.path.exists(str(attachment_path)):
            body_result = self.classify_email(body_text)
            policy = extract_policy_number(body_text)
            client = extract_client_name(body_text)
            
            item = WorkQueueItem(
                email_id=email_id,
                task_id=f"{email_id}_task_1",
                policy_number=policy,
                client_name=client,
                main_type=body_result.get("prediction", "unknown"),
                sub_type=body_result.get("prediction", "unknown"),
                pages="body_only",
                confidence=body_result.get("confidence", 0.0),
                source_attachment=""
            )
            queue = wq.route(item)
            
            return {
                "type": "single",
                "total_tasks": 1,
                "tasks": [item.to_dict()],
                "routed_to": queue
            }
        
        # --- Open and parse the PDF attachment page-by-page ---
        tasks = []
        try:
            reader = pypdf.PdfReader(attachment_path)
            
            current_task_pages = []     # Text content of pages in the current form
            current_start_page = 0      # 0-indexed start of the current form
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                current_task_pages.append(text)
                
                # Detect form boundary: "Declaration and Signature" marks the END of a form
                if "Declaration and Signature" in text:
                    combined_text = "\n".join(current_task_pages)
                    
                    # Extract structured fields from the PDF text
                    policy = extract_policy_number(combined_text)
                    client = extract_client_name(combined_text)
                    
                    # Classify this chunk (body text + PDF text for better signal)
                    chunk_classification = self.classify_email(combined_text)
                    
                    page_range = f"{current_start_page + 1}-{i + 1}"
                    task_id = f"{email_id}_task_{len(tasks) + 1}"
                    
                    item = WorkQueueItem(
                        email_id=email_id,
                        task_id=task_id,
                        policy_number=policy,
                        client_name=client,
                        main_type=chunk_classification.get("prediction", "unknown"),
                        sub_type=chunk_classification.get("prediction", "unknown"),
                        pages=page_range,
                        confidence=chunk_classification.get("confidence", 0.0),
                        source_attachment=str(attachment_path)
                    )
                    
                    queue = wq.route(item)
                    task_dict = item.to_dict()
                    task_dict["routed_to"] = queue
                    tasks.append(task_dict)
                    
                    # Reset for the next client's form
                    current_task_pages = []
                    current_start_page = i + 1
            
            # Handle any remaining pages that didn't end with a signature
            if current_task_pages:
                combined_text = "\n".join(current_task_pages)
                policy = extract_policy_number(combined_text)
                client = extract_client_name(combined_text)
                chunk_classification = self.classify_email(combined_text)
                
                item = WorkQueueItem(
                    email_id=email_id,
                    task_id=f"{email_id}_task_{len(tasks) + 1}",
                    policy_number=policy,
                    client_name=client,
                    main_type=chunk_classification.get("prediction", "unknown"),
                    sub_type=chunk_classification.get("prediction", "unknown"),
                    pages=f"{current_start_page + 1}-{len(reader.pages)}",
                    confidence=chunk_classification.get("confidence", 0.0),
                    source_attachment=str(attachment_path)
                )
                queue = wq.route(item)
                task_dict = item.to_dict()
                task_dict["routed_to"] = queue
                tasks.append(task_dict)
                    
            return {
                "type": "bulk" if len(tasks) > 1 else "single",
                "total_tasks": len(tasks),
                "tasks": tasks
            }
            
        except Exception as e:
            return {"type": "error", "message": f"Failed to parse PDF: {str(e)}"}

    def classify_email(self, text: str, attachments: List[str] = []) -> Dict[str, Any]:
        """
        Implements the 4-tier classification system for a specific text chunk.
        """
        for attachment in attachments:
            if "qr_type:" in attachment:
                schema_id = attachment.split("qr_type:")[1].split(".")[0]
                return {
                    "tier": 1,
                    "prediction": schema_id,
                    "confidence": 1.0,
                    "method": "deterministic_qr"
                }

        if self.tier4:
            result = self.tier4.predict(text)
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
