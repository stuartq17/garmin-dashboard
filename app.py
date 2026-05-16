import streamlit as st
import pandas as pd
import plotly.graph_objects as go

@st.cache_data
def load_data():
    return pd.read_parquet("data/df_daily_hrs.parquet")

df_daily_hrs = load_data()

df_daily_hrs = df_daily_hrs.copy()

# create x-axis variables

# convert from days to weeks
df_daily_hrs["x_start"] = df_daily_hrs["season_day"] / 7
df_daily_hrs["x_end"] = -df_daily_hrs["days_to_end"] / 7

metrics = ["run_avg_hr", "run_max_hr", "rest_hr"]

# UI controls

st.title("Heart Rate Across Training Cycles")

# enforce chronological season ordering
season_order = ["XC 2021", "Track 2022", "XC 2022", "Track 2023", "XC 2023", "Track 2024", "XC 2024", "Track 2025", "XC 2025", "Track 2026"]

# only keep seasons actually present
season_order = [s for s in season_order
                if s in df_daily_hrs["season"].unique()]

selected_seasons = st.multiselect("Seasons", season_order, default=season_order)

selected_metric = st.selectbox("Metric", metrics, index=2)

align = st.radio("Align", ["start", "end"], index = 1, horizontal=True)

# smoothing slider
window = st.slider("Smoothing (days)", 1, 30, 14, step=1)

# smoothing
df_smooth = df_daily_hrs.copy()

if window > 1:
  df_smooth = df_smooth.sort_values(["season", "date"])

  for m in metrics:
    df_smooth[m] = df_smooth.groupby("season")[m].transform(
        lambda s: s.rolling(window, center=True, min_periods=1).mean()
    )

# reshape for plotting

df_plot = df_smooth.melt(
  id_vars=["date", "season", "season_day", "days_to_end", "x_start", "x_end"],
  value_vars=metrics,
  var_name="metric",
  value_name="value").dropna()

# filter data
filtered = df_plot.copy()

filtered = filtered[filtered["season"].isin(selected_seasons)]

filtered = filtered[filtered["metric"] == selected_metric]

x_col = ("x_start" if align == "start" else "x_end")

# color map

colors = {"XC 2021": "#440154",
          "Track 2022": "#414487",
          "XC 2022": "#2A788E",
          "Track 2023": "#22A884",
          "XC 2023": "#7AD151",
          "Track 2024": "#BDDf26",
          "XC 2024": "#FDE725",
          "Track 2025": "#FCA636",
          "XC 2025": "#E16462",
          "Track 2026": "#B12A90"}

# create figure

fig = go.Figure()

for season in season_order:
  df_s = filtered[filtered["season"] == season].sort_values(x_col)

  if len(df_s) == 0:
    continue

  fig.add_trace(
    go.Scatter(
      x=df_s[x_col],
      y=df_s["value"],
      mode="lines",
      name=season,

      line=dict(width=3, color=colors.get(season)),

      customdata=df_s[["date", "season_day", "days_to_end"]].values,

      hovertemplate=("<b>%{fullData.name}</b><br><br>"
      "Date: %{customdata[0]}<br>"
      "Heart Rate: %{y:.1f} bpm<br>"
      "Season Day: %{customdata[1]}<br>"
      "Days To End: %{customdata[2]}<br>"
      "<extra></extra>")))

# axis labels
if align == "start":
    x_title = "Weeks After Start of Season"

else:
    x_title = "Negative Weeks Until End of Season"

metric_titles = {"run_avg_hr": "Average Run Heart Rate",
                 "run_max_hr": "Maximum Run Heart Rate",
                 "rest_hr": "Resting Heart Rate"}

# layout
fig.update_layout(template="plotly_white",
                  height=750,
                  hovermode="closest",
                  
                  xaxis_title=x_title,
                  yaxis_title="Heart Rate (bpm)",
                  legend_title="Season",
                  title=metric_titles[selected_metric])

fig.update_xaxes(showgrid=True, zeroline=True)

fig.update_yaxes(showgrid=True)

# display
st.plotly_chart(fig, use_container_width=True)
