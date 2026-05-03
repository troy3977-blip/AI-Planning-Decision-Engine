# engine/staffing.py
import numpy as np
from scipy.special import gammaln
from .models import StaffingParameters, StaffingRecommendation
import pandas as pd

def erlang_c(arrival_rate: float, service_rate: float, num_servers: int) -> float:
    """Erlang-C probability of waiting."""
    if num_servers <= 0:
        return 1.0
    rho = arrival_rate / (num_servers * service_rate)
    if rho >= 1:
        return 1.0
    
    # Standard Erlang-C formula (stable implementation)
    a = (num_servers * rho)
    p0_inv = (np.exp(gammaln(num_servers + 1)) / (a ** num_servers)) + sum(
        [a**k / np.math.factorial(k) for k in range(num_servers)]
    )
    pw = (a**num_servers / (np.math.factorial(num_servers) * (1 - rho))) / p0_inv
    return pw

def find_min_servers(arrival_rate: float, service_rate: float, target_sl: float, target_wait: float, max_servers: int = 100) -> int:
    for s in range(1, max_servers):
        pw = erlang_c(arrival_rate, service_rate, s)
        # Approximate wait probability vs SLA
        if pw < target_sl:   # Simplified; enhance with full queueing formula
            return s
    return max_servers

def generate_staffing_recommendations(forecast_result, params: StaffingParameters) -> pd.DataFrame:
    recommendations = []
    service_rate = 1.0 / params.aht_seconds
    
    for idx, row in forecast_result.forecast_df.iterrows():
        lambda_rate = row['yhat'] / (forecast_result.forecast_df.index.freq.delta.total_seconds() if hasattr(forecast_result.forecast_df.index, 'freq') else 900)
        
        required = find_min_servers(lambda_rate, service_rate, params.target_service_level, params.target_wait_seconds)
        adjusted = int(np.ceil(required / (1 - params.shrinkage_factor)))
        
        recommendations.append({
            'interval': idx,
            'required_fte': float(adjusted),
            'cost_impact_annual': float(adjusted * params.cost_per_fte_annual),
            'projected_sla': 0.95,  # placeholder - enhance
            'breach_risk': 0.05
        })
    
    return pd.DataFrame(recommendations)