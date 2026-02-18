# Configuration parameters for the LEO satellite visibility analysis.
# All simulation, filter, and hazard model parameters are defined here for easy adjustment.

# Simulation and Cache Settings
TLE_CACHE_FILE = "starlink_tle_latest.txt"  # File for caching downloaded TLE data
MIN_CACHE_AGE_HOURS = 3.0  # Minimum age (hours) before refreshing TLE cache

# Ground Location (Vijayawada Center)
GROUND_LAT_DEG = 16.5062  # Latitude in degrees
GROUND_LON_DEG = 80.6480  # Longitude in degrees
ELEV_MIN_DEG = 10.0  # Minimum elevation angle for visibility (degrees)

# Region and Usability Filter Parameters
MAX_GROUND_DISTANCE_KM = 300  # Max distance from ground terminal for satellite inclusion (km)
MIN_VISIBLE_SECONDS = 180  # Minimum visibility duration for a window (seconds)
MIN_AVG_ELEV_DEG = 30.0  # Minimum average elevation for a window (degrees)

# Time Settings
SIM_DURATION_S = 2 * 3600  # Simulation duration (seconds, e.g., 2 hours)
STEP_S = 15  # Time step for computations (seconds)
START_OFFSET_S = 60.0  # Initial time offset (seconds)

# Hazard Model Parameters (Tuned lower for realism)
ALPHA_GEO = 0.001  # Geometric hazard weight (scales tracking difficulty)
ALPHA_BEAM = 0.002  # Beam handover hazard weight (models handover sensitivity)
ALPHA_RAIN = 0.005  # Atmospheric hazard weight (elevation-dependent attenuation)
EPSILON = 1e-3  # Small epsilon for numerical stability (not used extensively)
OMEGA_TH = 1.2  # Angular-rate threshold for beam handover (deg/s)
LAMBDA_RISK = 0.6  # Risk-aversion parameter (balances reliability vs. duration)

# Sensitivity Analysis Variations
# Dictionary of parameters to vary and their test values
VARIATIONS = {
    'ELEV_MIN_DEG': [5.0, 15.0, 20.0],
    'MAX_GROUND_DISTANCE_KM': [200, 400, 500],
    'MIN_VISIBLE_SECONDS': [120, 240, 300],
    'MIN_AVG_ELEV_DEG': [12.0, 24.0, 30.0],
    'ALPHA_GEO': [0.0005, 0.001, 0.002],
    'ALPHA_BEAM': [0.001, 0.002, 0.004],
    'ALPHA_RAIN': [0.003, 0.005, 0.008],
    'LAMBDA_RISK': [0.3, 0.6, 1.0],
    'OMEGA_TH': [0.4, 1.2, 1.6]
}