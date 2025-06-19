# utils/gantt_chart.py
import streamlit as st
import pandas as pd
import plotly.express as px

def render_gantt_chart(forecast_text: str):
    import pandas as pd
    import plotly.express as px
    import streamlit as st

    rows = []
    parsing = False

    for line in forecast_text.splitlines():
        line = line.strip()
        if line.lower().startswith("month") and "severity" in line.lower():
            parsing = True
            continue
        if parsing and "|" in line and not line.startswith("-"):
            try:
                parts = [x.strip() for x in line.split("|")]
                if len(parts) >= 2:
                    date = parts[0]
                    desc = parts[1]
                    severity = "High" if "very high" in desc.lower() else \
                               "High" if "high" in desc.lower() else \
                               "Medium" if "medium" in desc.lower() else "Low"
                    rows.append({"Start": date, "Task": "Damage Evolution", "Severity": severity})
            except Exception:
                continue

    if not rows:
        st.info("No forecast data found for Gantt chart.")
        return

    df = pd.DataFrame(rows)
    df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
    df["Finish"] = df["Start"] + pd.to_timedelta(30, unit='d')

    color_map = {"High": "red", "Medium": "orange", "Low": "green"}
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Severity", color_discrete_map=color_map)
    fig.update_layout(title="Projected Deterioration Timeline", xaxis_title="Time", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

