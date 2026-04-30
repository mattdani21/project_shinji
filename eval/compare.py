import json
import os

def compare_runs(run_ids: list):
    reports = []
    for rid in run_ids:
        path = f"data/runs/{rid}_results.json"
        if not os.path.exists(path):
            print(f"Run {rid} not found.")
            continue
        with open(path, "r") as f:
            reports.append(json.load(f))
            
    if not reports:
        return
        
    html = "<html><head><title>Comparison Report</title></head><body>"
    html += "<h1>Evaluation Comparison</h1><table border='1'><tr>"
    
    keys = ["model_name", "total_samples", "accuracy", "ece", "auto_route_pct", "hc_accuracy", "avg_latency_ms"]
    
    html += "<th>Metric</th>"
    for r in reports:
        html += f"<th>{r['model_name']}</th>"
    html += "</tr>"
    
    for key in keys[1:]:
        html += f"<tr><td>{key}</td>"
        for r in reports:
            val = r[key]
            if isinstance(val, float):
                val = round(val, 4)
            html += f"<td>{val}</td>"
        html += "</tr>"
        
    html += "</table></body></html>"
    
    os.makedirs("eval/reports/comparisons", exist_ok=True)
    out_path = f"eval/reports/comparisons/comparison.html"
    with open(out_path, "w") as f:
        f.write(html)
        
    print(f"Comparison report saved to {out_path}")

if __name__ == "__main__":
    import sys
    runs = sys.argv[1:]
    if not runs:
        runs = ["dummy", "random", "gemini_ceiling"]
    compare_runs(runs)
