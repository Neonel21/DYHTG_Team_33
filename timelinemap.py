import pygame
import pandas as pd
import numpy as np
from data_sort import identifier
from config import WIDTH, HEIGHT
from dropdown import Dropdown
from data_processing import load_data, get_students_on_campus, is_student_allowed, initialise_building_locations
from drawing import draw_buildings, draw_students, draw_building_popup
from interactions import building_after_click

minutes = 0

selected_building = None
popup_close_rect = None
popup_rect = None

colour_flag = "none"

pygame.init()

canvas = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Map")
running = True
clock = pygame.time.Clock()

location_df, people_df, student_logs_df = load_data()

buildings = initialise_building_locations(location_df)

font = pygame.font.Font('freesansbold.ttf', 18)

colour_options = ["none", "year", "subject"]
colour_dropdown = Dropdown(10, 50, colour_options, selected=colour_options.index(colour_flag))

is_paused = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                is_paused = not is_paused
            elif event.key == pygame.K_ESCAPE:
                        selected_building = None
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            consumed, changed = colour_dropdown.handle_click(event.pos)

            if changed:
                colour_flag = colour_dropdown.value

            if not consumed:
                selected_building = building_after_click(event.pos, buildings, selected_building, 
                                                         popup_rect, popup_close_rect)

    if not is_paused:
        minutes = (minutes + 1) % 1440
        current_time = (minutes // 60) * 100 + minutes % 60
        students_to_show_df = get_students_on_campus(current_time, student_logs_df)
        students_to_show_df = is_student_allowed(students_to_show_df)

    canvas.fill((0, 0, 0))

    draw_buildings(canvas, location_df)
    draw_students(canvas, students_to_show_df, people_df, colour_flag)

    time_text = f"{minutes // 60:02d}:{minutes % 60:02d}"
    label = font.render(time_text, True, (255, 255, 255))
    canvas.blit(label, (10, 10))

    if selected_building:
        popup_rect, popup_close_rect = draw_building_popup(canvas, selected_building, location_df, students_to_show_df)

    colour_dropdown.draw(canvas)

    pygame.display.update()
    clock.tick(30)