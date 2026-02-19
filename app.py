import streamlit as st
from src.graphs import sankey_diagram, pie_chart, bar_chart
from src.data import load
st.set_page_config(page_title="Financial Dashboard", layout="wide")
st.title("Personal Financial Dashboard")
data = load()
st.header("Sankey Diagram")
sankey_fig = sankey_diagram(data)
st.plotly_chart(sankey_fig, use_container_width=True)
st.header("Pie Chart")
pie_fig = pie_chart(data)
st.plotly_chart(pie_fig, use_container_width=True)
st.header("Bar Chart")
bar_fig = bar_chart(data)
st.plotly_chart(bar_fig, use_container_width=True)
st.header("Forecasting Income")

# Improvement points for the code above:
# 1. Add error handling for data loading and visualization functions to manage potential issues gracefully.
# 2. Include user input options to customize the visualizations (e.g., date ranges
#    or categories) for a more interactive dashboard experience.
# 3. Implement caching for data loading and processing to enhance performance, especially with large datasets.
# 4. Add descriptive text or tooltips to explain each visualization for better user understanding.
# 5. Consider adding more visualizations or metrics, such as trend lines or comparisons over time, to provide deeper insights into the financial data.
# 6. Ensure responsiveness of the dashboard layout for different screen sizes and devices.
# 7. Include a summary section that highlights key financial metrics (e.g., total income, expenses, savings) at a glance.