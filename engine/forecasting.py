# engine/forecasting.py
import pandas as pd
from prophet import Prophet
import numpy as np
from .models import TimeSeriesData, ForecastResult


def load_and_preprocess(data: TimeSeriesData) -> pd.DataFrame:
    df = pd.DataFrame({
        'ds': pd.to_datetime(data.timestamp),
        'y': data.volume
    })
    df = df.set_index('ds')
    df = df.resample(f'{data.interval_minutes}min').sum().reset_index()
    df = df.drop_duplicates(subset=['ds']).sort_values('ds')
    return df


def generate_forecast(data: TimeSeriesData, horizon_days: int = 90) -> ForecastResult:
    """Generate Prophet forecast with floor protection for volume."""
    df = load_and_preprocess(data)
    
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=True,
        seasonality_mode='multiplicative',
        uncertainty_samples=800,
        interval_width=0.95
    )
    model.fit(df)
    
    freq_str = f"{data.interval_minutes}min"
    future = model.make_future_dataframe(
        periods=horizon_days * (1440 // data.interval_minutes),
        freq=freq_str
    )
    
    forecast = model.predict(future)
    
    # === PRODUCTION FLOOR PROTECTION ===
    # Workforce volume can never be negative or zero.
    # We apply a hard floor to prevent unrealistic inputs to the Erlang-C optimizer.
    MIN_VOLUME = 25.0
    forecast['yhat'] = forecast['yhat'].clip(lower=MIN_VOLUME)
    if 'yhat_lower' in forecast.columns:
        forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=MIN_VOLUME)
    
    base = forecast['yhat'].values
    
    # Probabilistic scenarios (also floored)
    scenarios = {
        "base": base,
        "optimistic": np.maximum(base * 0.85, MIN_VOLUME),
        "pessimistic": base * 1.20,                    # usually higher
        "high_volatility": np.maximum(
            base * (1 + 0.12 * np.random.randn(len(base))), 
            MIN_VOLUME
        )
    }
    
    return ForecastResult(
        forecast_df=forecast,
        scenarios=scenarios,
        horizon_days=horizon_days
    )