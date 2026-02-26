import pandas as pd
import plotly.graph_objects as go
from typing import Tuple, Optional
from .utils import hex_to_rgba, colors
from .forecasting import sarima

def sankey_diagram(data: pd.DataFrame) -> go.Figure:
    # Separate inflows and outflows
    inflows = data[data['amount'] > 0].groupby('concept')['amount'].sum().reset_index()
    outflows = data[data['amount'] < 0].copy()
    outflows['amount'] = -outflows['amount']  # make positive for Sankey

    # Layer 1: inflows
    layer1 = list(inflows['concept'])
    # Layer 2: aggregate Savings, Expenses, and Balance
    layer2 = ['Savings', 'Expenses', 'Balance']
    # Layer 3: detailed expenses
    detailed_expenses = list(outflows[outflows['concept'] != 'Savings']['concept'].unique())

    # Combine labels in order
    labels = layer1 + layer2 + detailed_expenses

    # --- Build links ---
    source_indices = []
    target_indices = []
    values = []
    link_colors = []

    # Compute totals
    total_savings = outflows[outflows['concept'] == 'Savings']['amount'].sum()
    total_expenses = outflows[outflows['concept'] != 'Savings']['amount'].sum()
    total_out = total_savings + total_expenses

    for i, inflow_row in inflows.iterrows():
        income_amount = inflow_row['amount']

        # Determine proportional allocation
        savings_amount = (income_amount * total_savings / total_out) if total_out > 0 else 0
        expenses_amount = (income_amount * total_expenses / total_out) if total_out > 0 else 0
        allocated = savings_amount + expenses_amount
        balance_amount = max(income_amount - allocated, 0)  # leftover goes to Balance

        # Layer 1 → Layer 2
        if savings_amount > 0:
            source_indices.append(labels.index(inflow_row['concept']))
            target_indices.append(labels.index('Savings'))
            values.append(savings_amount)
            link_colors.append('green')
        if expenses_amount > 0:
            source_indices.append(labels.index(inflow_row['concept']))
            target_indices.append(labels.index('Expenses'))
            values.append(expenses_amount)
            link_colors.append('blue')
        if balance_amount > 0:
            source_indices.append(labels.index(inflow_row['concept']))
            target_indices.append(labels.index('Balance'))
            values.append(balance_amount)
            link_colors.append('gray')

    # Layer 2 → Layer 3 (Expenses → detailed categories)
    for expense_row in outflows[outflows['concept'] != 'Savings'].itertuples():
        source_indices.append(labels.index('Expenses'))
        target_indices.append(labels.index(expense_row.concept))
        values.append(expense_row.amount)
        link_colors.append('red')

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="lightblue"
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=values,
            color=link_colors
        ))])

    fig.update_layout(title_text="Sankey Diagram Breakdown", font_size=10)
    return fig

def pie_chart(data: pd.DataFrame) -> go.Figure:
    expenses = data[data['amount'] < 0]
    category_sums = expenses.groupby('concept')['amount'].sum().abs().sort_values(ascending=False).reset_index()
    fig = go.Figure(data=[go.Pie(
        labels=category_sums['concept'],
        values=category_sums['amount'],
        hole=0.5,
        textinfo='percent+label',
        direction='clockwise',
        textposition='inside'
    )])
    fig.update_layout(
        title_text="Pie Chart of Expenses Distribution",
        width=800,
        height=800,
        showlegend=True
    )
    return fig

def bar_chart(data: pd.DataFrame) -> go.Figure:
    df = pd.DataFrame({
        'month_year': pd.to_datetime(data['date'], errors='coerce').dt.strftime('%b %Y'),
        'amount': data['amount']
    })

    monthly_sums = df.groupby('month_year', sort=False)['amount'].sum().reset_index()
    monthly_sums['datetime'] = pd.to_datetime(monthly_sums['month_year'], format='%b %Y')
    monthly_sums = monthly_sums.sort_values('datetime').reset_index(drop=True)

    fig = go.Figure(data=[go.Bar(
        x=monthly_sums['month_year'],
        y=monthly_sums['amount'],
        marker_color=monthly_sums['amount'].apply(lambda x: colors.green if x >= 0 else colors.red)
    )])

    fig.update_layout(
        title_text="Monthly Financial Overview",
        xaxis_title="Month",
        yaxis_title="Total amount"
    )
    return fig

def line_chart(
    data: pd.DataFrame,
    forecast_horizon: int = 3,
    sarima_order: Tuple[int, int, int] = (1, 1, 1),
    seasonal_order: Tuple[int, int, int, int] = (0, 1, 1, 12),
    frequency: Optional[str] = "ME",
) -> go.Figure:
    """
    Plot the cumulative income trend and overlay a SARIMA forecast.

    Parameters
    ----------
    data : pd.DataFrame
        Must contain columns ['Date', 'Income'] representing periodic income data.
    forecast_horizon : int, default=12
        Number of future periods (in `frequency` units) to forecast.
    sarima_order : tuple[int, int, int], default=(1, 1, 1)
        Non-seasonal (p, d, q) order for SARIMA model.
    seasonal_order : tuple[int, int, int, int], default=(0, 1, 1, 12)
        Seasonal (P, D, Q, s) order for SARIMA model.
    frequency : str, default="M"
        Pandas frequency string (e.g., 'M' for monthly, 'W' for weekly).
    transform : bool, default=True
        Whether to log-transform the income series before fitting the model
        (useful for stabilizing variance over time).

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure showing historical cumulative income and SARIMA forecast.
    """
    forecast = sarima(
        data=data,
        forecast_horizon=forecast_horizon,
        sarima_order=sarima_order,
        seasonal_order=seasonal_order,
        frequency=frequency
    )

    observed_cum = forecast['observed_cumulative']
    cum_forecast = forecast['cumulative']
    cum_ci = forecast['cumulative_ci']

    observed_cum.index = pd.to_datetime(observed_cum.index)
    cum_forecast.index = pd.to_datetime(cum_forecast.index)
    cum_ci.index = pd.to_datetime(cum_ci.index)

    if not observed_cum.empty and cum_forecast.index[0] > observed_cum.index[-1]:
        last_idx = observed_cum.index[-1]
        last_val = float(observed_cum.iloc[-1])
        cum_forecast = pd.concat([pd.Series([last_val], index=[last_idx]), cum_forecast])
        cum_ci = pd.concat([pd.DataFrame({'lower': [last_val], 'upper': [last_val]}, index=[last_idx]), cum_ci])

    fig = go.Figure()
    # Forecast
    fig.add_trace(go.Scatter(
        x=cum_forecast.index,
        y=cum_forecast.values,
        mode='lines+markers',
        name='SARIMA forecast',
        line=dict(color=hex_to_rgba(colors.forecast), dash='dash')
    ))
    # Forecast Confidence Interval
    fig.add_trace(go.Scatter(
        x=list(cum_ci.index) + list(cum_ci.index[::-1]),
        y=list(cum_ci['lower'].values) + list(cum_ci['upper'].values[::-1]),
        fill='toself',
        fillcolor=hex_to_rgba(colors.forecast, alpha=0.12),
        line=dict(color=hex_to_rgba(colors.forecast, alpha=0.12)),
        hoverinfo='skip',
        showlegend=True,
        name='95% CI'
    ))
    # Observed
    fig.add_trace(go.Scatter(
        x=observed_cum.index,
        y=observed_cum.values,
        mode='lines+markers',
        name='Observed',
        line=dict(color=hex_to_rgba(colors.observed))
    ))

    fig.update_layout(
        title_text="Cumulative Financial Trend with SARIMA Forecast",
        xaxis_title="Date",
        yaxis_title="Cumulative amount",
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    return fig
