from flask import Flask, jsonify
import pandas as pd
from src.graphs import sankey_diagram, pie_chart, bar_chart, line_chart

app = Flask(__name__)

# Mock data for visualizations
mock_data = pd.DataFrame({
    'concept': ['Salary', 'Investment', 'Rent', 'Groceries', 'Utilities'],
    'amount': [5000, 2000, -1500, -800, -300],
    'date': ['2026-01-01', '2026-01-15', '2026-02-01', '2026-02-15', '2026-03-01']
})

@app.route('/api/sankey', methods=['GET'])
def get_sankey_data():
    fig = sankey_diagram(mock_data)
    return jsonify(fig.to_plotly_json())

@app.route('/api/pie', methods=['GET'])
def get_pie_data():
    fig = pie_chart(mock_data)
    return jsonify(fig.to_plotly_json())

@app.route('/api/bar', methods=['GET'])
def get_bar_data():
    fig = bar_chart(mock_data)
    return jsonify(fig.to_plotly_json())

@app.route('/api/line', methods=['GET'])
def get_line_data():
    fig = line_chart(mock_data)
    return jsonify(fig.to_plotly_json())

if __name__ == '__main__':
    app.run(debug=True)