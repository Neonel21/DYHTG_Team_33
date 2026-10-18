import os, sys, time
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

import pygame
import streamlit as st

GAME_DIR = Path(__file__).parent / 'Tom_Game'
if str(GAME_DIR) not in sys.path:
    sys.path.insert(0, str(GAME_DIR))

pygame.init()

from config import WIDTH, HEIGHT
from data_processing import load_data, get_students_on_campus, is_student_allowed
from drawing import draw_buildings, draw_students, draw_building_popup
from dropdown import Dropdown
from key import build_key_entries, draw_key, KEY_GAP

COLOUR_OPTIONS = ['none', 'year', 'subject']

@st.cache_resource          # load once, so the random jitter doesn't change every click
def game_data():
    return load_data()

def draw_frame(minutes, colour_flag, selected_building=None):
    location_df, people_df, student_logs_df = game_data()
    canvas = pygame.Surface((WIDTH, HEIGHT))

    current_time = (minutes // 60) * 100 + minutes % 60
    students = is_student_allowed(get_students_on_campus(current_time, student_logs_df))

    canvas.fill((0, 0, 0))
    draw_buildings(canvas, location_df)
    draw_students(canvas, students, people_df, colour_flag)

    dropdown = Dropdown(10, 50, COLOUR_OPTIONS, selected=COLOUR_OPTIONS.index(colour_flag))
    draw_key(canvas, build_key_entries(colour_flag, people_df),
             dropdown.header_rect.x, dropdown.header_rect.bottom + KEY_GAP)

    font = pygame.font.Font('freesansbold.ttf', 18)
    canvas.blit(font.render(f'{minutes // 60:02d}:{minutes % 60:02d}', True, (255, 255, 255)), (10, 10))

    if selected_building:
        draw_building_popup(canvas, selected_building, location_df, students)
    dropdown.draw(canvas)

    frame = pygame.surfarray.array3d(canvas).swapaxes(0, 1)   # pygame (x, y) → image (row, col)
    outside = int((~students['within_hours']).sum()) if len(students) else 0
    return frame, len(students), outside

def render_pygame_tab():
    st.subheader('Campus timeline map')
    st.caption('Every dot is a student, every square a building. '
               'Red dots are students inside a building outside its opening hours.')

    location_df, _, _ = game_data()
    c1, c2, c3 = st.columns([1, 1, 2])
    colour_flag = c1.selectbox('Colour students by', COLOUR_OPTIONS, key='pg_colour')
    building = c2.selectbox('Inspect a building', ['None'] + sorted(location_df['Building Name']), key='pg_building')
    building = None if building == 'None' else building
    start = c3.select_slider('Time', options=list(range(0, 1440, 5)), value=22 * 60 + 10, key='pg_time',
                             format_func=lambda m: f'{m // 60:02d}:{m % 60:02d}')

    p1, p2 = st.columns([1, 3])
    play = p1.button('▶ Play from this time', key='pg_play')
    speed = p2.select_slider('Speed', options=[1, 2, 5, 10], value=5, key='pg_speed',
                             format_func=lambda s: f'{s} min / frame')

    left, right = st.columns([3, 1])
    image, stats = left.empty(), right.empty()

    def show(minutes):
        frame, on_campus, outside = draw_frame(minutes, colour_flag, building)
        image.image(frame, width=WIDTH)
        with stats.container():
            st.metric('Students on campus', on_campus)
            st.metric('Outside opening hours', outside)

    if play:                                  # animate until midnight
        for minutes in range(start, 1440, speed):
            show(minutes)
            time.sleep(0.06)
    else:
        show(start)

        