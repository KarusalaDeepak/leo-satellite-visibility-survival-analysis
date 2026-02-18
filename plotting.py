# Functions for plotting results and performing sensitivity analysis.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.stats import spearmanr
from visibility import compute_visibility_df

def plot_results(df, example_windows):
    """
    Generate plots for evaluation and validation.
    
    :param df: Visibility DataFrame.
    :param example_windows: Dict of example window data.
    """
    os.makedirs("figures", exist_ok=True)
    
    if df.empty:
        return

    # Plot 1: Scatter of Geometric Duration vs EUST
    plt.figure(figsize=(8, 6))
    plt.scatter(df['duration_s'], df['expected_service_s'], alpha=0.7)
    min_val = min(df['duration_s'].min(), df['expected_service_s'].min())
    max_val = max(df['duration_s'].max(), df['expected_service_s'].max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Equality')
    plt.xlabel('Geometric Duration (s)')
    plt.ylabel('Expected Usable Service Time (EUST, s)')
    plt.title('Geometric vs Risk-Aware Service Duration')
    plt.legend()
    plt.grid(True)
    plt.savefig('figures/fig1_geom_vs_eust_scatter.png')
    plt.close()

    # Plot 2: Scatter of Overestimation % vs Duration (changed from hist for better insight)
    overestimation_pct = ((df['duration_s'] - df['expected_service_s']) / df['duration_s']) * 100
    plt.figure(figsize=(8, 6))
    plt.scatter(df['duration_s'], overestimation_pct, alpha=0.7)
    plt.xlabel('Geometric Duration (s)')
    plt.ylabel('Overestimation (%)')
    plt.title('Geometric Overestimation vs Pass Duration')
    plt.grid(True)
    plt.savefig('figures/fig2_overestimation_hist.png')
    plt.close()

    # Plot 3: Survival Function and Hazard Components (for top window)
    if example_windows:
        top_sat = df.iloc[0]['satellite_id']
        best = example_windows.get(top_sat)
        if best:
            fig = plt.figure(figsize=(10, 7))
            plt.subplot(2, 1, 1)
            plt.plot(best["w_times"], best["h_geo"], label="Geo")
            plt.plot(best["w_times"], best["h_beam"], "--", label="Beam")
            plt.plot(best["w_times"], best["h_rain"], ":", label="Rain")
            plt.plot(best["w_times"], best["h_total"], lw=2, label="Total")
            plt.ylabel("Hazard Rate")
            plt.legend()
            plt.grid(True)

            plt.subplot(2, 1, 2)
            plt.plot(best["w_times"], best["survival"], lw=2)
            plt.xlabel("Time (s)")
            plt.ylabel("Survival Probability")
            plt.grid(True)

            plt.tight_layout()
            plt.savefig("figures/fig3_survival_and_hazards.png")
            plt.close()
            print("Fig. 3 saved: figures/fig3_survival_and_hazards.png")

def run_sensitivity_analysis(base_params, satellites, ts_times, ground, sim_start_wall, variations):
    """
    Perform sensitivity analysis by varying parameters.
    
    :param base_params: Base config dict.
    :param satellites: List of satellites.
    :param ts_times: Time array.
    :param ground: Ground location.
    :param sim_start_wall: Start time.
    :param variations: Dict of params to vary.
    :return: Sensitivity DataFrame.
    """
    sens_records = []
    base_df, _ = compute_visibility_df(base_params, satellites, ts_times, ground, sim_start_wall)
    if base_df.empty:
        return pd.DataFrame()
    base_agg = base_df.groupby('satellite_id')['utility'].max()
    base_top = base_agg.idxmax()

    for param, vals in variations.items():
        for val in vals:
            test_params = base_params.copy()
            test_params[param] = val
            test_df, _ = compute_visibility_df(test_params, satellites, ts_times, ground, sim_start_wall)
            if test_df.empty:
                sens_records.append({
                    'parameter': param,
                    'value': val,
                    'num_windows': 0,
                    'avg_utility': np.nan,
                    'top_sat_match': 0,
                    'rank_correlation': np.nan
                })
                continue
            num_win = len(test_df)
            avg_util = test_df['utility'].mean()
            test_agg = test_df.groupby('satellite_id')['utility'].max()
            common = base_agg.index.intersection(test_agg.index)
            corr = np.nan
            if len(common) > 1:
                corr, _ = spearmanr(base_agg.loc[common], test_agg.loc[common])
            top_match = 1 if test_agg.idxmax() == base_top else 0
            sens_records.append({
                'parameter': param,
                'value': val,
                'num_windows': num_win,
                'avg_utility': avg_util,
                'top_sat_id': test_agg.idxmax(),
                'top_sat_match': top_match,
                'rank_correlation': corr
            })

    sens_df = pd.DataFrame(sens_records)
    return sens_df

def plot_sensitivity(sens_df, variations):
    """
    Generate sensitivity plots for each varied parameter.
    
    :param sens_df: Sensitivity DataFrame.
    :param variations: Dict of varied params.
    """
    def plot_for_param(param, df):
        sub = df[df['parameter'] == param].sort_values('value')
        if sub.empty:
            return

        plt.figure(figsize=(10, 8))
        plt.subplot(2, 2, 1)
        plt.plot(sub['value'], sub['num_windows'], marker='o', color='red')
        plt.ylabel("Num Windows")
        plt.grid(True)

        plt.subplot(2, 2, 2)
        plt.plot(sub['value'], sub['avg_utility'], marker='s', color='red')
        plt.ylabel("Avg Utility")
        plt.grid(True)

        plt.subplot(2, 2, 3)
        plt.plot(sub['value'], sub['top_sat_match'], marker='^', color='red')
        plt.ylabel("Top-Sat Stability")
        plt.ylim(-0.05, 1.05)
        plt.grid(True)

        plt.subplot(2, 2, 4)
        plt.plot(sub['value'], sub['rank_correlation'], marker='d', color='red')
        plt.ylabel("Rank Correlation")
        plt.ylim(0, 1.05)
        plt.grid(True)

        plt.suptitle(f"Sensitivity to {param}")
        plt.tight_layout()
        plt.savefig(f"figures/fig4_sensitivity_{param.lower()}.png")
        plt.close()

    for p in variations.keys():
        plot_for_param(p, sens_df)