import pygame
import pandas as pd
import numpy as np
import random

width, height = 700, 700
building_colour = (255, 255, 255)
building_width = 30
building_width_half = building_width/2
student_radius = 2
student_colour = (0, 255, 0)
current_time = 0
minutes = 0

def strip_times(column):
    times = column.str.split("-", expand=True).astype(int)
    return times

def normalise_lat_lon(location_df):
    min_lat, min_lon = (location_df["lat"].min(), location_df["lon"].min())
    max_lat, max_lon = (location_df["lat"].max(), location_df["lon"].max())

    location_df["lat"] = (location_df["lat"] - min_lat)/(max_lat - min_lat)*(width-100)+50
    location_df["lon"] = (location_df["lon"] - min_lon)/(max_lon - min_lon)*(height-100)+50
    return location_df

def get_students_on_campus(current_time, student_logs_df):
    times = strip_times(student_logs_df["Time"])
    start = times[0]
    end = times[1].replace(0, 2400)

    normal = (start <= current_time) & (current_time <= end)
    overnight = (current_time >= start) | (current_time <= end)
    mask = np.where(start <= end, normal, overnight)
    students_to_show_df = student_logs_df[mask]
    return students_to_show_df

def get_student_locations(security_logs_df, location_df):
    location_small = location_df[["Building Name", "lat", "lon", "Opening Times"]]

    merged = security_logs_df.merge(
        location_small, left_on="Location", right_on="Building Name", how="left"
    )
    merged = merged.drop(columns="Building Name")
    # Offsets for aesthetics and differtiating students inside buildings
    n = len(merged)
    merged["lat"] += np.random.uniform(-building_width_half+1, building_width_half-1, n)
    merged["lon"] += np.random.uniform(-building_width_half+1, building_width_half-1, n)
    return merged

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
                    | ((start + 2400 >= start_openings) & (end + 2400 <= end_openings)))
    students_log["within_hours"] = within_hours
    return students_log
    

def draw_buildings(location_df):
    for name, lat, lon in zip(location_df["Building Name"], location_df["lat"], location_df["lon"]):
        building = pygame.Rect(lat-building_width_half, lon-building_width_half, building_width, building_width)
        pygame.draw.rect(canvas, building_colour, building)

def draw_students(students):
    for lat, lon, within_hours, id in zip(students["lat"], students["lon"], students["within_hours"], students["Student ID"]):
        if not within_hours:
            colour = (255, 0, 0)
            # print(id)
        else:
            colour = student_colour
        pygame.draw.circle(canvas, colour, (lat, lon), student_radius)



location_df = pd.read_csv("location_data.csv")

coords = location_df["Geolocation"].str.strip("{}").str.split(expand=True).astype(float)
location_df[["lat", "lon"]] = coords
location_df = normalise_lat_lon(location_df)

people_df = pd.read_csv("people_data.csv")

security_logs_df = pd.read_csv("security_logs.csv")

student_logs_df = get_student_locations(security_logs_df, location_df)

# print(get_student_locations(security_logs_df, location_df))

# print(get_students_on_campus(1200, student_logs_df))
pygame.init()

canvas = pygame.display.set_mode((width, height))

pygame.display.set_caption("Map")
exit = False
clock = pygame.time.Clock()

font = pygame.font.Font('freesansbold.ttf', 18)

while not exit:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit = True
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.get_pos()

    minutes = (minutes + 1) % 1440 # wraps at 24 hours
    current_time = (minutes // 60) * 100 + minutes % 60 # 0-1439 -> 0000-2359

    students_to_show_df = get_students_on_campus(current_time, student_logs_df)
    students_to_show_df = is_student_allowed(students_to_show_df)

    canvas.fill((0, 0, 0))

    draw_buildings(location_df)
    draw_students(students_to_show_df)

    time_text = f"{minutes // 60:02d}:{minutes % 60:02d}"
    label = font.render(time_text, True, (255, 255, 255))
    canvas.blit(label, (10, 10))    
    pygame.display.update()
    clock.tick(30)