import pygame
import pandas as pd
import numpy as np
from data_sort import identifier
from config import *
from dropdown import Dropdown

width, height = 700, 700
building_colour = (60, 66, 80)
building_width = 30
building_width_half = building_width/2
student_radius = 2
current_time = 0
minutes = 0

selected_building = None
popup_close_rect = None
popup_rect = None

colour_flag = "none"


def wrap_text(text, font, max_width):
    lines, line = [], ""
    for word in str(text).split():
        test = f"{line} {word}".strip()
        # font.size() returns (width, height) in pixels
        if font.size(test)[0] <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines

def draw_building_popup(name, location_df, students_now_df):
    info = location_df[location_df["Building Name"] == name]
    if info.empty:
        return None, None
    info = info.iloc[0]

    inside = students_now_df[students_now_df["Location"] == name]
    violations = int((~inside["within_hours"]).sum()) if not inside.empty else 0
    violators = inside[~inside["within_hours"]]
    violation_names = violators["Name"].astype(str).tolist()
    

    text_width = POPUP_WIDTH - POPUP_PADDING * 2
    body_lines = [
        f"Opening times: {info['Opening Times']}",
        f"Students inside now: {len(inside)}",
        "",
    ]
    if violation_names:
        body_lines += ["Outside opening hours:"]
        body_lines += [f"  {n}" for n in violation_names[:10]]
        if len(violation_names) > 10:
            body_lines.append(f"  ... and {len(violation_names) - 10} more")
        body_lines += [""]

    popup_height = POPUP_PADDING * 2 + POPUP_TITLE_HEIGHT + len(body_lines) * POPUP_LINE_HEIGHT
    popup_rect = pygame.Rect(
        (canvas.get_width() - POPUP_WIDTH) // 2,
        (canvas.get_height() - popup_height) // 2,
        POPUP_WIDTH,
        popup_height,
    )

    pygame.draw.rect(canvas, POPUP_BACKGROUND, popup_rect, border_radius=POPUP_CORNER_RADIUS)
    pygame.draw.rect(canvas, POPUP_BORDER, popup_rect,
                     width=POPUP_BORDER_WIDTH, border_radius=POPUP_CORNER_RADIUS)

    title = title_font.render(name, True, POPUP_TITLE_COLOUR)
    canvas.blit(title, (popup_rect.x + POPUP_PADDING, popup_rect.y + POPUP_PADDING))

    close_rect = pygame.Rect(
        popup_rect.right - POPUP_CLOSE_SIZE - POPUP_CLOSE_MARGIN,
        popup_rect.y + POPUP_CLOSE_MARGIN,
        POPUP_CLOSE_SIZE,
        POPUP_CLOSE_SIZE,
    )
    close_label = popup_font.render("X", True, POPUP_CLOSE_COLOUR)
    canvas.blit(close_label, close_label.get_rect(center=close_rect.center))

    first_line_y = popup_rect.y + POPUP_PADDING + POPUP_TITLE_HEIGHT
    for i, line in enumerate(body_lines):
        text = popup_font.render(line, True, POPUP_TEXT_COLOUR)
        canvas.blit(text, (popup_rect.x + POPUP_PADDING, first_line_y + i * POPUP_LINE_HEIGHT))

    return popup_rect, close_rect

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
    merged["lat"] += np.random.uniform(-building_width_half+2, building_width_half-2, n)
    merged["lon"] += np.random.uniform(-building_width_half+2, building_width_half-2, n)
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
                    | ((start + 2400 >= start_openings) & (end_openings + 2400 <= end_openings)))
    students_log["within_hours"] = within_hours
    return students_log

def colour_code_students(id, students):
    if colour_flag == "none":
            return STUDENT_COLOURS[0]
    
    student = students[students["Student ID"] == id]
    if student.empty:
        return STUDENT_COLOURS[0]
    student = student.iloc[0]

    if colour_flag == "year":
        year_of_study = student["Year of Study"]
        colour = STUDENT_COLOURS[int(year_of_study)]
        return colour
    
    if colour_flag == "subject":
        subject = student["Subject"]
        if subject in SUBJECTS:
            i = SUBJECTS.index(subject)
        else:
            i = 30
        return STUDENT_COLOURS[i]

    return STUDENT_COLOURS[0]


def initialise_building_locations(location_df):
    buildings_array = []
    for name, lat, lon in zip(location_df["Building Name"], location_df["lat"], location_df["lon"]):
        buildings_array.append([name, lat, lon])
    return buildings_array

def clicked_on_building(mouse_pos, buildings):
    for building in buildings:
        x = mouse_pos[0]
        y = mouse_pos[1]
        lat = building[1]
        lon = building[2]
        if (x >= lat-building_width_half and x <= lat+building_width_half
            and y >= lon-building_width_half and y <= lon+building_width_half):
            return building
    return None

def draw_buildings(location_df):
    for name, lat, lon in zip(location_df["Building Name"], location_df["lat"], location_df["lon"]):
        building = pygame.Rect(lat-building_width_half, lon-building_width_half, building_width, building_width)
        pygame.draw.rect(canvas, building_colour, building)

def draw_students(students):
    for lat, lon, within_hours, id in zip(students["lat"], students["lon"], students["within_hours"], students["Student ID"]):
        if not within_hours:
            colour = VIOLATION_COLOUR
            # print(id)
        else:
            colour = colour_code_students(id, people_df)
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
running = True
clock = pygame.time.Clock()

buildings = initialise_building_locations(location_df)

font = pygame.font.Font('freesansbold.ttf', 18)

popup_font = pygame.font.SysFont("consolas", 16)
title_font = pygame.font.SysFont("consolas", 22, bold=True)

colour_options = ["none", "year", "subject"]
colour_dropdown = Dropdown(10, 50, colour_options, selected=colour_options.index(colour_flag))

is_paused = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            is_paused = not is_paused
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            consumed, changed = colour_dropdown.handle_click(event.pos)

            if changed:
                colour_flag = colour_dropdown.value

            if not consumed:
                if selected_building and popup_close_rect and popup_close_rect.collidepoint(event.pos):
                    selected_building = None
                else:
                    hit = clicked_on_building(event.pos, buildings)
                    if hit is not None:
                        selected_building = hit[0]
                    elif selected_building and popup_rect and not popup_rect.collidepoint(event.pos):
                        selected_building = None
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            selected_building = None


    if not is_paused:
        minutes = (minutes + 1) % 1440
        current_time = (minutes // 60) * 100 + minutes % 60
        students_to_show_df = get_students_on_campus(current_time, student_logs_df)
        students_to_show_df = is_student_allowed(students_to_show_df)

    canvas.fill((0, 0, 0))

    draw_buildings(location_df)
    draw_students(students_to_show_df)

    time_text = f"{minutes // 60:02d}:{minutes % 60:02d}"
    label = font.render(time_text, True, (255, 255, 255))
    canvas.blit(label, (10, 10))

    if selected_building:
        popup_rect, popup_close_rect = draw_building_popup(selected_building, location_df, students_to_show_df)

    colour_dropdown.draw(canvas)

    pygame.display.update()
    clock.tick(30)