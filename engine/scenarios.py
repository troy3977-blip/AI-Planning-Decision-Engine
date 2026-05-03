# engine/scenarios.py
"""
Bridge between forecasting, staffing, and the AI decision layer.
Generates multiple business scenarios ready for AI reasoning.
"""
from typing import List
from datetime import datetime
import pandas as pd
from .forecasting import generate_forecast
from .staffing import generate_staffing_recommendations
from .models import TimeSeriesData, StaffingParameters
from ai.schema import Scenario


def create_scenarios(
    time_series: TimeSeriesData,
    staffing_params: StaffingParameters,
    horizon_days: int = 30
) -> List[Scenario]:
    """
    Generate multiple scenarios (Base, Optimistic, Pessimistic) with staffing plans.
    """
    # 1. Generate forecast
    forecast = generate_forecast(time_series, horizon_days=horizon_days)
    
    # 2. Generate staffing recommendations
    staffing_df = generate_staffing_recommendations(forecast, staffing_params)
    
    avg_fte = staffing_df['required_fte'].mean()
    avg_cost = staffing_df['cost_impact_annual'].mean()
    
    scenarios = []
    
    for name, volume_multiplier, risk_adjust in [
        ("Base", 1.0, 0.08),
        ("Optimistic", 0.85, 0.04),
        ("Pessimistic", 1.25, 0.22)
    ]:
        fte = round(avg_fte * volume_multiplier, 1)
        cost = round(avg_cost * volume_multiplier, 0)
        
        scenarios.append(Scenario(
            scenario_id=f"SC_{name.upper()}",
            name=name,
            fte_required=fte,
            cost_annual=cost,
            expected_sla=0.93 if volume_multiplier <= 1.0 else 0.76,
            breach_risk=risk_adjust,
            occupancy_peak=0.87,
            notes=f"Volume multiplier: {volume_multiplier}x"
        ))
    
    return scenarios