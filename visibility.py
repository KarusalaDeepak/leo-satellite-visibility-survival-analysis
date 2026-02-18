# Core functions for computing satellite visibility windows, hazards, and metrics.

import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import spearmanr
from utils import compute_elevation, compute_angular_rate, great_circle_distance_km

def compute_visibility_df(params, satellites, ts_times, ground, sim_start_wall):
    """
    Compute visibility DataFrame for satellites based on parameters.
    
    :param params: Dict of config parameters.
    :param satellites: List of EarthSatellite objects.
    :param ts_times: Skyfield time array.
    :param ground: WGS84 location.
    :param sim_start_wall: Simulation start wall time.
    :return: Tuple (DataFrame of results, dict of example windows for plotting).
    """
    # Extract params for clarity
    ELEV_MIN_DEG = params['ELEV_MIN_DEG']
    MAX_GROUND_DISTANCE_KM = params['MAX_GROUND_DISTANCE_KM']
    MIN_VISIBLE_SECONDS = params['MIN_VISIBLE_SECONDS']
    MIN_AVG_ELEV_DEG = params['MIN_AVG_ELEV_DEG']
    STEP_S = params['STEP_S']
    ALPHA_GEO = params['ALPHA_GEO']
    ALPHA_BEAM = params['ALPHA_BEAM']
    ALPHA_RAIN = params['ALPHA_RAIN']
    LAMBDA_RISK = params['LAMBDA_RISK']
    OMEGA_TH = params['OMEGA_TH']

    # Filter satellites by region and usability
    region_sats = []
    sat_min_dist = {}
    for sat in satellites:
        elev_deg = compute_elevation(sat, ts_times, ground)
        vis = elev_deg >= ELEV_MIN_DEG
        vis_time_s = np.sum(vis) * STEP_S
        if vis_time_s < MIN_VISIBLE_SECONDS:
            continue
        vis_elev = elev_deg[vis]
        if len(vis_elev) == 0 or np.mean(vis_elev) < MIN_AVG_ELEV_DEG:
            continue
        vis_idx = np.where(vis)[0]
        geocentric = sat.at(ts_times[vis_idx])
        sub = geocentric.subpoint()
        dists_km = great_circle_distance_km(
            ground.latitude.degrees, ground.longitude.degrees,  # Fixed: Use ground lat/lon
            sub.latitude.degrees, sub.longitude.degrees
        )
        min_d = float(np.min(dists_km))
        if min_d <= MAX_GROUND_DISTANCE_KM:
            region_sats.append(sat)
            sat_min_dist[sat.name] = min_d

    records = []
    example_windows = {}  # Store data for top 3 windows by utility for plotting
    all_times = np.arange(params['START_OFFSET_S'], params['START_OFFSET_S'] + params['SIM_DURATION_S'] + STEP_S, STEP_S)  # Recompute time grid

    for sat in region_sats:
        elev_deg = compute_elevation(sat, ts_times, ground)
        elev_rad = np.radians(np.clip(elev_deg, 0.1, 90))  # Clip to avoid sin(0) issues
        ang_rate = compute_angular_rate(elev_rad, STEP_S)
        visible = elev_deg >= ELEV_MIN_DEG
        idx = 0
        while idx < len(all_times):
            if not visible[idx]:
                idx += 1
                continue
            start_idx = idx
            while idx < len(all_times) and visible[idx]:
                idx += 1
            end_idx = idx - 1
            w_times = all_times[start_idx:end_idx+1]
            w_dur = w_times[-1] - w_times[0]
            if w_dur < MIN_VISIBLE_SECONDS:
                continue
            w_elev_deg = elev_deg[start_idx:end_idx+1]
            if np.mean(w_elev_deg) < MIN_AVG_ELEV_DEG:
                continue
            w_elev_rad = elev_rad[start_idx:end_idx+1]
            w_rate = ang_rate[start_idx:end_idx+1]

            # Hazard components (as per survival analysis model)
            h_geo = np.clip(ALPHA_GEO * np.abs(w_rate) / np.maximum(np.sin(w_elev_rad), 0.1), 0, 0.05)  # Geometric hazard
            t_mod = (sim_start_wall + w_times) % 60
            near_ho = (np.mod(t_mod, 15) < 1.5).astype(float)  # Narrow spike for handover proxy
            h_beam = ALPHA_BEAM * near_ho * (np.abs(w_rate) > OMEGA_TH)  # Beam handover hazard
            h_rain = ALPHA_RAIN * np.exp(-w_elev_deg / 15.0)  # Atmospheric (rain) hazard, softer decay
            h_total = h_geo + h_beam + h_rain  # Composite hazard

            # Cumulative hazard (trapezoidal integration)
            cum_h = np.cumsum((h_total[:-1] + h_total[1:]) / 2 * STEP_S)
            cum_h = np.insert(cum_h, 0, 0.0)
            survival = np.exp(-cum_h)  # Survival function

            # Metrics
            exp_service = np.trapezoid(survival, dx=STEP_S)  # Expected Usable Service Time (EUST)
            var_service = np.trapezoid(survival * (1 - survival), dx=STEP_S)  # Variance (bounded uncertainty)
            utility = exp_service - LAMBDA_RISK * var_service  # Risk-adjusted utility
            drop_prob = 1.0 - survival[-1] if len(survival) > 0 else 0.0  # Drop probability

            # Record data
            record = {
                "satellite_id": sat.name,
                "start_time_utc": datetime.fromtimestamp(sim_start_wall + w_times[0]).isoformat(),
                "end_time_utc": datetime.fromtimestamp(sim_start_wall + w_times[-1]).isoformat(),
                "duration_s": float(w_dur),
                "expected_service_s": float(exp_service),
                "variance_s": float(var_service),
                "utility": float(utility),
                "avg_elevation_deg": float(np.mean(w_elev_deg)),
                "max_angular_rate_degs": float(np.max(np.abs(w_rate))),
                "drop_probability": drop_prob,
                "min_ground_dist_km": sat_min_dist.get(sat.name, np.nan),
            }
            records.append(record)

            # Store for plotting (all for now; filter to top 3 later)
            example_windows[sat.name] = {
                'w_times': w_times - w_times[0],  # Normalize to start at 0
                'survival': survival,
                'h_geo': h_geo,
                'h_beam': h_beam,
                'h_rain': h_rain,
                'h_total': h_total,
                'utility': utility
            }

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values("utility", ascending=False)
        # Filter example_windows to top 3 by utility
        top_sats = df['satellite_id'].head(3).values
        example_windows = {k: v for k, v in example_windows.items() if k in top_sats}
    return df, example_windows

def evaluate_results(df):
    """
    Compute additional evaluation metrics from visibility DataFrame.
    
    :param df: Visibility DataFrame.
    :return: None (prints metrics).
    """
    if df.empty:
        return
    overestimation_pct = ((df['duration_s'] - df['expected_service_s']) / df['duration_s']) * 100
    avg_overestimation = overestimation_pct.mean()
    median_overestimation = overestimation_pct.median()
    avg_drop_prob = df['drop_probability'].mean()
    print("\n--- Additional Evaluation Metrics ---")
    print(f"Average overestimation (%): {avg_overestimation:.2f}")
    print(f"Median overestimation (%): {median_overestimation:.2f}")
    print(f"Average drop probability: {avg_drop_prob:.4f}")
    
    # Geometric vs risk-aware ranking correlation
    geom_rank = df.sort_values('duration_s', ascending=False)['satellite_id'].values
    risk_rank = df['satellite_id'].values
    rank_corr, _ = spearmanr(df.sort_values('duration_s', ascending=False).index, df.index)
    print(f"Spearman rank correlation (geometric vs risk-aware): {rank_corr:.4f}")
