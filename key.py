import pygame
from config import STUDENT_COLOURS, SUBJECTS, VIOLATION_COLOUR
 
pygame.font.init()

KEY_GAP = 10

KEY_SWATCH_SIZE = 14
KEY_ROW_HEIGHT = 22
KEY_PADDING = 8
KEY_BORDER_WIDTH = 1
 
KEY_BACKGROUND = (30, 33, 40)
KEY_BORDER = (95, 102, 118)
KEY_TEXT_COLOUR = (220, 220, 225)
 
OTHER_SUBJECT_INDEX = 30
 
key_font = pygame.font.SysFont("consolas", 16)
 
 
def build_key_entries(colour_flag, people_df):
    if colour_flag == "year":
        years = sorted(people_df["Year of Study"].dropna().astype(int).unique())
        entries = [(f"Year {year}", STUDENT_COLOURS[year]) for year in years]
 
    elif colour_flag == "subject":
        subjects_in_data = set(people_df["Subject"].dropna())
        entries = [
            (name, STUDENT_COLOURS[i])
            for i, name in enumerate(SUBJECTS)
            if name in subjects_in_data
        ]
        if subjects_in_data - set(SUBJECTS):
            entries.append(("Other", STUDENT_COLOURS[OTHER_SUBJECT_INDEX]))
 
    else:
        entries = [("Student", STUDENT_COLOURS[0])]
 
    entries.append(("Outside opening hours", VIOLATION_COLOUR))
    return entries
 
 
def draw_key(surface, entries, x, y):
    text_width = max(key_font.size(label)[0] for label, _ in entries)
    panel_width = KEY_PADDING * 3 + KEY_SWATCH_SIZE + text_width
    panel_height = KEY_PADDING * 2 + len(entries) * KEY_ROW_HEIGHT
 
    panel = pygame.Rect(x, y, panel_width, panel_height)
 
    pygame.draw.rect(surface, KEY_BACKGROUND, panel)
    pygame.draw.rect(surface, KEY_BORDER, panel, width=KEY_BORDER_WIDTH)
 
    for i, (label, colour) in enumerate(entries):
        row_centre_y = panel.y + KEY_PADDING + i * KEY_ROW_HEIGHT + KEY_ROW_HEIGHT // 2

        swatch_centre = (panel.x + KEY_PADDING + KEY_SWATCH_SIZE // 2, row_centre_y)
        pygame.draw.circle(surface, colour, swatch_centre, KEY_SWATCH_SIZE // 2)
 

        text = key_font.render(label, True, KEY_TEXT_COLOUR)
        text_left = panel.x + KEY_PADDING * 2 + KEY_SWATCH_SIZE
        surface.blit(text, text.get_rect(midleft=(text_left, row_centre_y)))