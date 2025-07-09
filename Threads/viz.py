import pandas as pnd
import plotly.express as plx
import plotly.graph_objects as gro
from plotly.subplots import make_subplots
import os

# wind data in
df = pnd.read_csv("data/turbine_readings.csv")
# warp timestamps
df["timestamp"] = pnd.to_datetime(df["timestamp"])

# prep average curve
wind_by_time = df.groupby("timestamp")["wind_speed_mps"].mean().reset_index()
# ready histogram
wind_hist = df["wind_speed_mps"]

# latest snapshots per turbine
latest = df.sort_values("timestamp").groupby("turbine_id").last().reset_index()

# assemble canvas
fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"type": "scattermapbox"}, {"type": "xy"}],
        [{"type": "xy"}, None]],
    subplot_titles=("Turbine Locations", "Avg Wind Speed Over Time", "Wind Speed Distribution"),
    vertical_spacing=0.2
)

# drizzle map
map_fig = plx.scatter_mapbox(
    latest,
    lat="latitude",
    lon="longitude",
    hover_name="turbine_id",
    size=latest["power_output_kw"].clip(lower=0.1),
    color="wind_speed_mps",
    color_continuous_scale="Viridis",
    zoom=3
)
fig.add_trace(map_fig.data[0], row=1, col=1)

# paint line
fig.add_trace(
    gro.Scatter(
        x=wind_by_time["timestamp"],
        y=wind_by_time["wind_speed_mps"],
        mode="lines",
        name="Avg Wind Speed"
    ),
    row=1, col=2
)

# stack histogram
fig.add_trace(
    gro.Histogram(
        x=wind_hist,
        nbinsx=30,
        name="Wind Speed Distribution"
    ),
    row=2, col=1
)

# final polish
fig.update_layout(
    height=800,
    width=1200,
    title_text="Wind Turbine Performance Dashboard",
    mapbox_style="open-street-map",
    showlegend=False
)

# drop to disk
os.makedirs("outputs", exist_ok=True)
fig.write_html("outputs/dashboard.html")
fig.write_image("outputs/screenshot.png")

print("Dashboard saved to outputs/dashboard.html and screenshot.png")
