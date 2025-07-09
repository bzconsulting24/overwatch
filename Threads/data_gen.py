import pandas as pnd
import numpy as npy
import os
from datetime import datetime as dtm, timedelta as dt

# data dir
os.makedirs("data", exist_ok=True)

# params
num_turbines = 50
hours_per_day = 24
days = 7
total_rows = num_turbines * hours_per_day * days

# seed rng
npy.random.seed(42)

# turbine loc
turbine_ids = [f"TURB_{i+1:03d}" for i in range(num_turbines)]
latitudes   = npy.random.uniform(30.0, 45.0, num_turbines)
longitudes  = npy.random.uniform(-120.0, -90.0, num_turbines)

# timestamps
start_time = dtm(2024, 6, 1)
timestamps = [start_time + dt(hours=i) for i in range(hours_per_day * days)]

# build records
records = []
for tidx, tid in enumerate(turbine_ids):
    lat = latitudes[tidx]
    lon = longitudes[tidx]
    for t in timestamps:
        wind_speed   = max(0, npy.random.normal(8, 3))
        power_output = min(3000, wind_speed**3 + npy.random.normal(0, 200))
        temp         = npy.random.normal(15, 5)
        records.append({
            "turbine_id":      tid,
            "timestamp":       t.isoformat(),
            "latitude":        round(lat, 4),
            "longitude":       round(lon, 4),
            "wind_speed_mps":  round(wind_speed, 2),
            "power_output_kw": round(power_output, 1),
            "temperature_c":   round(temp, 1)
        })

# save csv
df = pnd.DataFrame(records)
df.to_csv("data/turbine_readings.csv", index=False)
print(" Data saved to data/turbine_readings.csv")