import pandas as pd
from typing import Tuple, Dict, Optional
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import warnings

def sarima(
    data: pd.DataFrame,
    forecast_horizon: int = 30,
    sarima_order: Tuple[int, int, int] = (1, 1, 1),
    seasonal_order: Tuple[int, int, int, int] = (0, 1, 1, 12),
    frequency: Optional[str] = 'ME'
) -> Dict[str, pd.Series]:
    """
    Fit a SARIMA model to an employee's periodic income series and produce forecasts.

    Parameters
    ----------
    data : pd.DataFrame
        Must contain columns ['date', 'amount'] representing observed income amounts
        over time at a consistent frequency.
    forecast_horizon : int, default=30
        Number of future periods (in `frequency` units) to forecast.
    sarima_order : tuple[int, int, int], default=(1, 1, 1)
        Non-seasonal (p, d, q) order for SARIMA.
    seasonal_order : tuple[int, int, int, int], default=(0, 1, 1, 12)
        Seasonal (P, D, Q, s) order for SARIMA.
    frequency : str, optional
        Pandas frequency string (e.g., 'M' for monthly, 'W' for weekly, 'D' for daily).
        If None, inferred from the date index.
    transform : bool, default=True
        Whether to log-transform income before fitting the model.
        Helps stabilize variance for upward-trending series.

    Returns
    -------
    dict
        Dictionary containing:
        - 'daily': pd.Series → Predicted income per period.
        - 'daily_ci': pd.DataFrame → 95% confidence interval for period income.
        - 'cumulative': pd.Series → Forecasted cumulative income.
        - 'cumulative_ci': pd.DataFrame → Confidence interval for cumulative income.
        - 'observed_cumulative': pd.Series → Observed cumulative income.
        - 'freq': str → Frequency used for modeling.

    Notes
    -----
    • Assumes income data is regular and typically monthly (salaried).
    • Recommended seasonal period: 12 for monthly pay.
    • Use `transform=False` if values are already stable (e.g., constant salary).
    """

    df = data.copy()
    balance = df.set_index('date')['balance'].sort_index()
    balance = balance.groupby(balance.index).last()

    full_index = pd.date_range(start=balance.index.min(), end=balance.index.max(), freq=frequency)
    observed_cumulative = balance.reindex(full_index).ffill().fillna(0.0)
    observed_cumulative.index.name = 'date'

    period_amounts = observed_cumulative.diff().fillna(observed_cumulative.iloc[0])
    period_amounts.index.name = 'date'

    last_obs = observed_cumulative.index[-1]
    forecast_index = pd.date_range(
        last_obs + pd.tseries.frequencies.to_offset(frequency),
        periods=forecast_horizon,
        freq=frequency
    )

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', ConvergenceWarning)
        warnings.simplefilter('ignore', UserWarning)

        model = SARIMAX(
            period_amounts,
            order=sarima_order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        res = model.fit(disp=False)
        pred = res.get_forecast(steps=forecast_horizon)

        daily_forecast = pred.predicted_mean
        daily_ci = pred.conf_int(alpha=0.05)
        daily_forecast.index = forecast_index
        daily_ci.index = forecast_index
        daily_ci.columns = ['lower', 'upper']

    last_cum = observed_cumulative.iloc[-1] if len(observed_cumulative) > 0 else 0.0
    cum_forecast = last_cum + daily_forecast.cumsum()

    cum_lower = last_cum + daily_ci['lower'].cumsum()
    cum_upper = last_cum + daily_ci['upper'].cumsum()
    cumulative_ci = pd.DataFrame({'lower': cum_lower, 'upper': cum_upper}, index=forecast_index)

    return {
        'daily': daily_forecast,
        'daily_ci': daily_ci,
        'cumulative': cum_forecast,
        'cumulative_ci': cumulative_ci,
        'observed_cumulative': observed_cumulative,
        'frequency': frequency
    }