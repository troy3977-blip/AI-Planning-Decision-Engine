# engine/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any

class TimeSeriesData(BaseModel):
    timestamp: List[datetime]
    volume: List[float]          # calls, tickets, sales, etc.
    interval_minutes: int = 15
    metadata: Optional[Dict[str, Any]] = None

class ForecastResult(BaseModel):
    forecast_df: Any                  # pandas DataFrame
    scenarios: Dict[str, Any]         # e.g., {"base": series, "pessimistic": series}
    horizon_days: int

class StaffingParameters(BaseModel):
    aht_seconds: int = 180
    target_service_level: float = 0.80   # e.g., 80% in 20s
    target_wait_seconds: int = 20
    cost_per_fte_annual: float = 65000
    shrinkage_factor: float = 0.15       # vacations, training, etc.

class StaffingRecommendation(BaseModel):
    interval: datetime
    required_fte: float
    cost_impact_annual: float
    projected_sla: float
    breach_risk: float