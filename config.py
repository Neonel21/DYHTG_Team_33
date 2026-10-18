import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent

WIDTH, HEIGHT = 700, 700
BUILDING_COLOUR = (60, 66, 80)
BUILDING_WIDTH = 30
BUILDING_WIDTH_HALF = BUILDING_WIDTH/2
STUDENT_RADIUS = 2

STUDENT_COLOURS = [
    (0, 200, 80),     # green
    (0, 120, 255),    # blue
    (255, 220, 0),    # yellow
    (170, 80, 255),   # purple
    (0, 220, 220),    # cyan
    (120, 255, 120),  # light green
    (255, 255, 255),  # white
    (135, 206, 250),  # sky blue
    (60, 90, 255),    # royal blue
    (190, 255, 0),    # lime
    (0, 255, 170),    # mint
    (0, 160, 150),    # teal
    (120, 120, 255),  # periwinkle
    (200, 160, 255),  # lavender
    (140, 60, 220),   # violet
    (255, 100, 255),  # magenta
    (220, 120, 200),  # mauve
    (160, 200, 60),   # olive green
    (255, 190, 60),   # amber
    (210, 210, 110),  # khaki
    (150, 255, 200),  # pale mint
    (70, 200, 140),   # sea green
    (100, 230, 255),  # light cyan
    (90, 140, 200),   # steel blue
    (80, 60, 200),    # indigo
    (230, 230, 180),  # cream
    (100, 255, 60),   # bright green
    (150, 230, 40),   # yellow-green
    (255, 240, 100),  # pale yellow
    (160, 160, 160),  # grey
    (110, 110, 170),  # slate
    (60, 180, 255),   # azure
    (180, 100, 160),  # muted orchid
    (130, 200, 180),  # seafoam
    (230, 160, 255),  # light orchid
]

VIOLATION_COLOUR = (255, 0, 0)

people_df = pd.read_csv(BASE_DIR / "people_data.csv")
SUBJECTS = sorted(people_df["Subject"].dropna().astype(str).unique())
# SUBJECTS = [
#     "Philosophy",
#     "Veterinary Medicine",
#     "Biomechanical Engineering",
#     "Medicine",
#     "Computing Science",
#     "English Literature",
#     "Mathematics",
#     "Physics",
#     "Chemistry",
#     "Education",
#     "Business"
# ]

SOCIETIES = [
    "Bad Movie Society",
    "Glasgow Students' Nightline",
    "Accapella Society",
    "Astrology Society",
    "Astronomy Society",
    "Big Band Society",
    "Back to Yoga Society",
    "Brunei Society",
    "Clash Of Clans Society",
    "Esports Society",
    "Cymdeithas Cymry Glasgow",
    "Dr Who Society",
    "FemEng Society",
    "Extinction Rebellion",
    "Grim Reaper Quidditch Club",
    "Italian Society",
    "Juggling Society",
    "Glasgow Latin America Society",
    "Volleyball Society",
    "LGBTQ+ Students Assoication",
    "Marxist Society",
    "Minecraft Society",
    "Motorcycling Society",
    "pHd Society",
    "Philosophy Society",
    "Pole Dancing Club",
    "Sexpression",
    "Shrek Society",
    "Soup Society",
    "Rising Stars",
    "Glasgow Uni Tech Society",
    "Skate Society",
]