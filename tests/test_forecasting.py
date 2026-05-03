# tests/test_forecasting.py
"""
Unit and integration tests for the SmartWFM Lite Forecasting Engine.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from engine.models import TimeSeriesData, ForecastResult
from engine.forecasting import load_and_preprocess, generate_forecast


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_time_series() -> TimeSeriesData:
    """7-day sample with stronger floor to prevent negatives."""
    start = datetime(2026, 5, 1, 8, 0)
    timestamps = [start + timedelta(minutes=15 * i) for i in range(7 * 96)]
    
    base = 120
    volume = []
    for i, ts in enumerate(timestamps):
        hour = ts.hour
        weekday = ts.weekday()
        daily_factor = 1.0 + 0.35 * np.sin(2 * np.pi * hour / 24)
        weekend_factor = 0.5 if weekday >= 5 else 1.0
        noise = np.random.normal(0, 7)
        val = max(35.0, base * daily_factor * weekend_factor + noise)   # Stronger floor
        volume.append(float(val))
    
    return TimeSeriesData(
        timestamp=timestamps,
        volume=volume,
        interval_minutes=15
    )


@pytest.fixture
def sample_forecast_result(sample_time_series) -> ForecastResult:
    return generate_forecast(sample_time_series, horizon_days=14)


# =============================================================================
# Tests
# =============================================================================

def test_load_and_preprocess(sample_time_series):
    df = load_and_preprocess(sample_time_series)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['ds', 'y']
    assert pd.api.types.is_datetime64_any_dtype(df['ds'])
    assert (df['y'] >= 35).all()          # Matches fixture floor
    assert not df.isnull().any().any()


def test_generate_forecast_basic_properties(sample_forecast_result):
    result = sample_forecast_result
    assert isinstance(result, ForecastResult)
    assert len(result.scenarios) == 4


def test_forecast_contains_future_predictions(sample_forecast_result):
    assert len(sample_forecast_result.forecast_df) > 500


def test_scenario_consistency(sample_forecast_result):
    """All scenarios must be positive - critical for staffing."""
    for name, series in sample_forecast_result.scenarios.items():
        series_array = np.asarray(series)
        assert (series_array > 0).all(), f"Scenario '{name}' contains non-positive values"


def test_probabilistic_scenarios_differ(sample_forecast_result):
    base = np.asarray(sample_forecast_result.scenarios["base"])
    opt = np.asarray(sample_forecast_result.scenarios["optimistic"])
    pes = np.asarray(sample_forecast_result.scenarios["pessimistic"])
    
    assert (opt < base * 0.96).any()
    assert (pes > base * 1.04).any()


def test_full_forecast_to_scenarios_integration(sample_time_series):
    result = generate_forecast(sample_time_series, horizon_days=30)
    assert len(result.scenarios["base"]) > 1000
    print(f"✓ Successfully generated {len(result.scenarios)} scenarios")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])