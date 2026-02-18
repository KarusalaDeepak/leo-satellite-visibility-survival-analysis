# Utility functions for TLE handling, orbital computations, and math helpers.

import numpy as np
import requests
import os
from datetime import datetime, timedelta
from skyfield.api import EarthSatellite, load, wgs84, utc

def get_fresh_tle_lines(tle_cache_file, min_cache_age_hours):
    """
    Fetch or load cached Starlink TLE data.
    
    :param tle_cache_file: Path to cache file.
    :param min_cache_age_hours: Max age before refresh.
    :return: List of TLE lines.
    """
    if os.path.exists(tle_cache_file):
        mod_time = datetime.fromtimestamp(os.path.getmtime(tle_cache_file))
        age = datetime.now() - mod_time
        if age < timedelta(hours=min_cache_age_hours):
            print(f"Using cached TLE (age: {age.total_seconds()/3600:.1f} h)")
            with open(tle_cache_file, 'r') as f:
                return f.read().strip().splitlines()
    
    print("Downloading fresh Starlink TLEs...")
    try:
        resp = requests.get(
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
            timeout=30
        )
        resp.raise_for_status()
        tle_text = resp.text.strip()
        with open(tle_cache_file, 'w') as f:
            f.write(tle_text)
        print("TLEs cached.")
        return tle_text.splitlines()
    except Exception as e:
        print(f"Download failed: {e}")
        if os.path.exists(tle_cache_file):
            print("Falling back to cache.")
            with open(tle_cache_file, 'r') as f:
                return f.read().strip().splitlines()
        raise RuntimeError("No TLE data available.")

def load_satellites(tle_lines, ts):
    """
    Load EarthSatellite objects from TLE lines.
    
    :param tle_lines: List of TLE lines.
    :param ts: Skyfield timescale object.
    :return: List of EarthSatellite objects.
    """
    satellites = []
    i = 0
    while i < len(tle_lines) - 2:
        name = tle_lines[i].strip()
        l1 = tle_lines[i + 1].strip()
        l2 = tle_lines[i + 2].strip()
        try:
            satellites.append(EarthSatellite(l1, l2, name, ts))
        except:
            pass
        i += 3
    return satellites

def compute_elevation(sat, times, ground):
    """
    Compute elevation angles for a satellite over time.
    
    :param sat: EarthSatellite object.
    :param times: Skyfield time array.
    :param ground: WGS84 location.
    :return: Numpy array of elevation degrees.
    """
    diff = sat - ground
    topo = diff.at(times)
    elev, _, _ = topo.altaz()
    return elev.degrees

def compute_angular_rate(elev_rad, dt):
    """
    Compute angular rate of elevation change.
    
    :param elev_rad: Elevation in radians.
    :param dt: Time step (seconds).
    :return: Angular rate in deg/s.
    """
    if len(elev_rad) < 2:
        return np.zeros_like(elev_rad)
    return np.gradient(elev_rad, dt) * (180 / np.pi)  # Convert to deg/s

def great_circle_distance_km(lat1_deg, lon1_deg, lat2_deg, lon2_deg):
    """
    Compute great-circle distance between two points on Earth.
    
    :param lat1_deg, lon1_deg: First point coordinates.
    :param lat2_deg, lon2_deg: Second point coordinates.
    :return: Distance in km.
    """
    R = 6371.0
    lat1 = np.radians(lat1_deg)
    lon1 = np.radians(lon1_deg)
    lat2 = np.radians(lat2_deg)
    lon2 = np.radians(lon2_deg)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c