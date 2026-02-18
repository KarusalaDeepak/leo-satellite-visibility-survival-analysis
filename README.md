# LEO Satellite Visibility Windows Using Survival Analysis

This repository contains the code for evaluating risk-aware LEO satellite visibility windows using survival analysis, based on real Starlink TLE data. It computes visibility metrics, performs sensitivity analysis, and generates plots.

## Dependencies
- Python 3.12+
- Libraries: numpy, pandas, requests, skyfield, scipy, matplotlib
- Install via: `pip install numpy pandas requests skyfield scipy matplotlib`

## How to Run
1. Clone the repo: `git clone https://github.com/yourusername/leo-satellite-visibility-survival-analysis.git`
2. Navigate to the directory: `cd leo-satellite-visibility-survival-analysis`
3. Run the main script: `python main.py`
   - This will download fresh TLEs if needed, compute visibility, run sensitivity analysis, generate CSVs, and save plots to `figures/`.

## Files
- `main.py`: Entry point for running the full analysis.
- `config.py`: Configuration parameters (e.g., simulation settings, hazard params).
- `utils.py`: Utility functions (e.g., TLE loading, elevation computation).
- `visibility.py`: Core visibility computation functions.
- `plotting.py`: Functions for generating plots.
- `regional_starlink_risk_aware_visibility.csv`: Sample base results.
- `sensitivity_results.csv`: Sample sensitivity analysis results.
- `figures/`: Sample generated plots.

## Results
The code generates CSV files and plots as described in the paper. Sample results are included for reference.

## License
MIT License (or your choice).
