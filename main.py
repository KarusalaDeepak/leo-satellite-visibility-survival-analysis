# Main entry point for running the LEO satellite visibility analysis.
# Loads config, computes visibility, evaluates, runs sensitivity, and plots.

import numpy as np
import time
import pandas as pd
from datetime import datetime
from skyfield.api import load, wgs84, utc
from config import *  # Import all params from config.py
from utils import get_fresh_tle_lines, load_satellites
from visibility import compute_visibility_df, evaluate_results
from plotting import plot_results, run_sensitivity_analysis, plot_sensitivity
from utils import great_circle_distance_km  # Imported if needed elsewhere

# Start simulation timer
sim_start_wall = time.time()

# Load timescale and ground location
ts = load.timescale()
ground = wgs84.latlon(GROUND_LAT_DEG, GROUND_LON_DEG)

# Time grid
all_times = np.arange(START_OFFSET_S, START_OFFSET_S + SIM_DURATION_S + STEP_S, STEP_S)
t0_utc = datetime.utcnow().replace(tzinfo=utc)
ts_times = ts.utc(
    t0_utc.year, t0_utc.month, t0_utc.day,
    t0_utc.hour, t0_utc.minute,
    t0_utc.second + all_times
)

# Load satellites
print("Loading Starlink satellites...")
tle_lines = get_fresh_tle_lines(TLE_CACHE_FILE, MIN_CACHE_AGE_HOURS)
satellites = load_satellites(tle_lines, ts)
print(f"Loaded {len(satellites)} satellites")

# Base parameters dict (from config)
base_params = {
    'ELEV_MIN_DEG': ELEV_MIN_DEG,
    'MAX_GROUND_DISTANCE_KM': MAX_GROUND_DISTANCE_KM,
    'MIN_VISIBLE_SECONDS': MIN_VISIBLE_SECONDS,
    'MIN_AVG_ELEV_DEG': MIN_AVG_ELEV_DEG,
    'STEP_S': STEP_S,
    'START_OFFSET_S': START_OFFSET_S,
    'SIM_DURATION_S': SIM_DURATION_S,
    'ALPHA_GEO': ALPHA_GEO,
    'ALPHA_BEAM': ALPHA_BEAM,
    'ALPHA_RAIN': ALPHA_RAIN,
    'LAMBDA_RISK': LAMBDA_RISK,
    'OMEGA_TH': OMEGA_TH
}

# Compute base case
print("Computing base case...")
df, example_windows = compute_visibility_df(base_params, satellites, ts_times, ground, sim_start_wall)
df.to_csv("regional_starlink_risk_aware_visibility.csv", index=False)
print("\n--- Base Results Summary ---")
print(f"Windows found: {len(df)}")
print(f"Runtime: {time.time() - sim_start_wall:.1f} s")
if not df.empty:
    print(df.head(8)[["satellite_id", "duration_s", "expected_service_s",
                      "utility", "drop_probability", "avg_elevation_deg"]])

# Evaluate additional metrics
evaluate_results(df)

# Run sensitivity analysis
print("\nRunning sensitivity analysis...")
sens_df = run_sensitivity_analysis(base_params, satellites, ts_times, ground, sim_start_wall, VARIATIONS)
sens_df.to_csv('sensitivity_results.csv', index=False)
print("\nSensitivity summary (grouped by parameter):")
print(sens_df.groupby('parameter')[['num_windows', 'avg_utility',
                                    'top_sat_match', 'rank_correlation']].mean())

# Generate plots
print("\nGenerating plots...")
plot_results(df, example_windows)
plot_sensitivity(sens_df, VARIATIONS)

print("\nAll done. Results saved to:")
print(" • regional_starlink_risk_aware_visibility.csv")
print(" • sensitivity_results.csv")
print(" • figures/ directory")
