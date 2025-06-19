# utils/forecast_chart.py
import pandas as pd
import plotly.express as px
import streamlit as st

def render_forecast_chart(forecast_text):
    lines = [line for line in forecast_text.splitlines() if "20" in line]
    rows = []
    for line in lines:
        parts = line.split(":")
        if len(parts) == 2:
            month, severity = parts[0].strip(), parts[1].strip().lower()
            severity_score = {"low": 1, "medium": 2, "high": 3}.get(severity, 0)
            rows.append((month, severity_score))

    if rows:
        df = pd.DataFrame(rows, columns=["Month", "Severity Score"])
        fig = px.line(df, x="Month", y="Severity Score", markers=True)
        st.plotly_chart(fig)
