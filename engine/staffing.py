# engine/staffing.py
import numpy as np
from math import factorial as math_factorial
import pandas as pd

from .models import StaffingParameters


def erlang_c(arrival_rate: float, service_rate: float, num_servers: int) -> float:
    """Safe Erlang-C formula."""
    if num_servers <= 0 or service_rate <= 0:
        return 1.0
    
    rho = arrival_rate / (num_servers * service_rate)
    if rho >= 0.99:   # Avoid instability near 1.0
        return 1.0
    
    a = arrival_rate / service_rate
    sum_term = sum(a**k / math_factorial(k) for k in range(num_servers))
    
    numerator = a**num_servers / math_factorial(num_servers)
    pw = (numerator / (1 - rho)) / (sum_term + numerator / (1 - rho))
    return min(1.0, max(0.0, pw))


def find_min_servers(arrival_rate: float, service_rate: float, target_sl: float, target_wait: float, max_servers: int = 100) -> int:
    """Find minimal servers."""
    for s in range(1, max_servers + 1):
        pw = erlang_c(arrival_rate, service_rate, s)
        if pw <= (1 - target_sl):
            return s
    return max_servers


def generate_staffing_recommendations(forecast_result, params: StaffingParameters) -> pd.DataFrame:
    """Generate staffing recommendations with safety guards."""
    if params.aht_seconds <= 0:
        params = params.model_copy()
        params.aht_seconds = 180  # fallback
    
    recommendations = []
    service_rate = 1.0 / params.aht_seconds
    interval_seconds = 900  # 15 min
    
    for idx, row in forecast_result.forecast_df.iterrows():
        lambda_rate = max(0.1, row['yhat'] / interval_seconds)  # prevent zero
        
        required = find_min_servers(
            lambda_rate, 
            service_rate, 
            params.target_service_level, 
            params.target_wait_seconds
        )
        
        adjusted_fte = max(1, int(np.ceil(required / (1 - max(0.01, params.shrinkage_factor)))))
        
        recommendations.append({
            'interval': idx,
            'required_fte': float(adjusted_fte),
            'cost_impact_annual': float(adjusted_fte * params.cost_per_fte_annual),
            'projected_sla': min(0.98, params.target_service_level + 0.05),
            'breach_risk': max(0.02, 0.18 - params.target_service_level)
        })
    
    return pd.DataFrame(recommendations)