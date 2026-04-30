import cv2
import numpy as np
import fitz # PyMuPDF
import json
import os
from typing import List, Dict, Any, Optional

class Tier1QRRouter:
    def __init__(self):
        self.detector = cv2.QRCodeDetector()

    def scan_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Scans every page of a PDF for QR codes.
        Returns a list of decoded payloads, one per page.
        """
        results = []
        doc = fitz.open(pdf_path)
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            # Render page to image (pixmap)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better QR detection
            img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            
            # Convert to grayscale for OpenCV
            if pix.n == 4: # RGBA
                gray = cv2.cvtColor(img_data, cv2.COLOR_RGBA2GRAY)
            else: # RGB
                gray = cv2.cvtColor(img_data, cv2.COLOR_RGB2GRAY)
                
            # Detect and decode QR
            data, bbox, _ = self.detector.detectAndDecode(gray)
            
            if data:
                try:
                    payload = json.loads(data)
                    payload["page_index"] = i
                    results.append(payload)
                except json.JSONDecodeError:
                    # Fallback for old simple format if any
                    results.append({"raw_data": data, "page_index": i})
            else:
                results.append({"page_index": i, "no_qr": True})
                
        doc.close()
        return results

    def analyze_completeness(self, qr_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups pages into forms and identifies missing pages.
        """
        forms = []
        current_form = None
        
        for res in qr_results:
            if res.get("no_qr"):
                # If we hit a page with no QR, we might need Tier 4
                if current_form:
                    # In our system, every page of a new form should have a QR
                    # If it doesn't, it might be an un-indexed page in the middle or end
                    current_form["pages_found"].append(res["page_index"] + 1)
                continue
                
            form_type = res.get("sub_type")
            page_num = res.get("page")
            total_pages = res.get("total_pages")
            policy = res.get("policy")
            
            # If we see page 1, it's a new form boundary
            if page_num == 1 or current_form is None:
                if current_form:
                    forms.append(self._finalize_form(current_form))
                
                current_form = {
                    "sub_type": form_type,
                    "policy": policy,
                    "total_pages_expected": total_pages,
                    "pages_found": [page_num],
                    "actual_page_indices": [res["page_index"]],
                    "status": "processing"
                }
            else:
                # Append to current form
                current_form["pages_found"].append(page_num)
                current_form["actual_page_indices"].append(res["page_index"])
                
        if current_form:
            forms.append(self._finalize_form(current_form))
            
        return forms

    def _finalize_form(self, form: Dict[str, Any]) -> Dict[str, Any]:
        expected = set(range(1, form["total_pages_expected"] + 1))
        found = set(form["pages_found"])
        missing = sorted(list(expected - found))
        
        form["pages_missing"] = missing
        if not missing:
            form["status"] = "complete"
            form["confidence"] = 1.0
        else:
            form["status"] = "incomplete"
            form["confidence"] = 0.8 # Lower confidence if pages missing
            form["rfi_note"] = f"Page(s) {', '.join(map(str, missing))} of {form['total_pages_expected']} missing."
            
        return form

if __name__ == "__main__":
    # Quick test if a file exists
    import sys
    if len(sys.argv) > 1:
        router = Tier1QRRouter()
        results = router.scan_pdf(sys.argv[1])
        analysis = router.analyze_completeness(results)
        print(json.dumps(analysis, indent=2))
