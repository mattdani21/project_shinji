import numpy as np

def calculate_accuracy(predictions, ground_truths):
    if len(predictions) == 0: return 0.0
    correct = sum(1 for p, g in zip(predictions, ground_truths) if p == g)
    return correct / len(predictions)

def calculate_ece(confidences, predictions, ground_truths, n_bins=10):
    """Expected Calibration Error"""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    ece = 0.0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = [(c, p, g) for c, p, g in zip(confidences, predictions, ground_truths) 
                  if bin_lower < c <= bin_upper]
        if not in_bin: continue
        
        bin_acc = sum(1 for c, p, g in in_bin if p == g) / len(in_bin)
        bin_conf = sum(c for c, p, g in in_bin) / len(in_bin)
        
        ece += (len(in_bin) / len(predictions)) * abs(bin_acc - bin_conf)
        
    return ece

def calculate_auto_route(confidences, predictions, ground_truths, threshold=0.9):
    """Percentage of predictions above confidence threshold, and their accuracy."""
    high_conf = [(p, g) for c, p, g in zip(confidences, predictions, ground_truths) if c >= threshold]
    if len(predictions) == 0 or len(high_conf) == 0: return 0.0, 0.0
    
    route_pct = len(high_conf) / len(predictions)
    acc_at_hc = sum(1 for p, g in high_conf if p == g) / len(high_conf)
    
    return route_pct, acc_at_hc
