import numpy as np
import pandas as pd
from config import WIDTH, HEIGHT, BUILDING_WIDTH_HALF
from pathlib import Path

BASE_DIR = Path(__file__).parent

def strip_times(column):
    times = column.str.split("-", expand=True).astype(int)
    return times

def normalise_lat_lon(location_df):
    min_lat, min_lon = (location_df["lat"].min(), location_df["lon"].min())
    max_lat, max_lon = (location_df["lat"].max(), location_df["lon"].max())

    location_df["lat"] = (location_df["lat"] - min_lat)/(max_lat - min_lat)*(WIDTH-100)+50
    location_df["lon"] = (location_df["lon"] - min_lon)/(max_lon - min_lon)*(HEIGHT-100)+50
    return location_df



def get_student_locations(security_logs_df, location_df):
    location_small = location_df[["Building Name", "lat", "lon", "Opening Times"]]

    merged = security_logs_df.merge(
        location_small, left_on="Location", right_on="Building Name", how="left"
    )
    merged = merged.drop(columns="Building Name")
    # Offsets for aesthetics and differtiating students inside buildings
    n = len(merged)
    merged["lat"] += np.random.uniform(-BUILDING_WIDTH_HALF+2, BUILDING_WIDTH_HALF-2, n)
    merged["lon"] += np.random.uniform(-BUILDING_WIDTH_HALF+2, BUILDING_WIDTH_HALF-2, n)
    return merged

def get_students_on_campus(current_time, student_logs_df):
    times = strip_times(student_logs_df["Time"])
    start = times[0]
    end = times[1].replace(0, 2400)

    normal = (start <= current_time) & (current_time <= end)
    overnight = (current_time >= start) | (current_time <= end)
    mask = np.where(start <= end, normal, overnight)
    students_to_show_df = student_logs_df[mask]
    return students_to_show_df

def is_student_allowed(students_log):
    if students_log.empty:
        return students_log.assign(within_hours=pd.Series(dtype=bool))
    
    students_log = students_log.copy()

    times = strip_times(students_log["Time"])
    start = times[0]
    end = times[1].replace(0, 2400)
    end = end.where(end>=start, end + 2400)

    opening_times = strip_times(students_log["Opening Times"])
    start_openings = opening_times[0]
    end_openings = opening_times[1].replace(0, 2400)
    end_openings = end_openings.where(end_openings>=start_openings, end + 2400)

    always_open = (start_openings == 0) & (end_openings == 2400)

    within_hours = always_open | (((start >= start_openings) & (end <= end_openings)) 
                    | ((start + 2400 >= start_openings) & (end_openings + 2400 <= end_openings)))
    students_log["within_hours"] = within_hours
    return students_log

def load_data():
    location_df = pd.read_csv(BASE_DIR / "location_data.csv")

    coords = location_df["Geolocation"].str.strip("{}").str.split(expand=True).astype(float)
    location_df[["lat", "lon"]] = coords
    location_df = normalise_lat_lon(location_df)

    people_df = pd.read_csv(BASE_DIR / "people_data.csv")

    security_logs_df = pd.read_csv(BASE_DIR / "security_logs.csv")

    student_logs_df = get_student_locations(security_logs_df, location_df)

    return location_df, people_df, student_logs_df

def initialise_building_locations(location_df):
    buildings_array = []
    for name, lat, lon in zip(location_df["Building Name"], location_df["lat"], location_df["lon"]):
        buildings_array.append([name, lat, lon])
    return buildings_array