from config import BUILDING_COLOUR, BUILDING_WIDTH, BUILDING_WIDTH_HALF, VIOLATION_COLOUR, STUDENT_RADIUS
import pygame
from colours import colour_code_students

pygame.font.init()

popup_font = pygame.font.SysFont("consolas", 16)
title_font = pygame.font.SysFont("consolas", 22, bold=True)

# Popup layout
POPUP_WIDTH = 360
POPUP_PADDING = 14
POPUP_TITLE_HEIGHT = 36
POPUP_LINE_HEIGHT = 22
POPUP_CLOSE_SIZE = 22
POPUP_CLOSE_MARGIN = 8
POPUP_CORNER_RADIUS = 8
POPUP_BORDER_WIDTH = 2

# Popup colours
POPUP_BACKGROUND = (30, 33, 40)
POPUP_BORDER = (95, 102, 118)
POPUP_TITLE_COLOUR = (240, 240, 245)
POPUP_TEXT_COLOUR = (210, 210, 215)
POPUP_CLOSE_COLOUR = (200, 200, 205)

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

def draw_building_popup(surface, name, location_df, students_now_df):
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
        (surface.get_width() - POPUP_WIDTH) // 2,
        (surface.get_height() - popup_height) // 2,
        POPUP_WIDTH,
        popup_height,
    )

    pygame.draw.rect(surface, POPUP_BACKGROUND, popup_rect, border_radius=POPUP_CORNER_RADIUS)
    pygame.draw.rect(surface, POPUP_BORDER, popup_rect,
                     width=POPUP_BORDER_WIDTH, border_radius=POPUP_CORNER_RADIUS)

    title = title_font.render(name, True, POPUP_TITLE_COLOUR)
    surface.blit(title, (popup_rect.x + POPUP_PADDING, popup_rect.y + POPUP_PADDING))

    close_rect = pygame.Rect(
        popup_rect.right - POPUP_CLOSE_SIZE - POPUP_CLOSE_MARGIN,
        popup_rect.y + POPUP_CLOSE_MARGIN,
        POPUP_CLOSE_SIZE,
        POPUP_CLOSE_SIZE,
    )
    close_label = popup_font.render("X", True, POPUP_CLOSE_COLOUR)
    surface.blit(close_label, close_label.get_rect(center=close_rect.center))

    first_line_y = popup_rect.y + POPUP_PADDING + POPUP_TITLE_HEIGHT
    for i, line in enumerate(body_lines):
        text = popup_font.render(line, True, POPUP_TEXT_COLOUR)
        surface.blit(text, (popup_rect.x + POPUP_PADDING, first_line_y + i * POPUP_LINE_HEIGHT))

    return popup_rect, close_rect

def draw_buildings(surface, location_df):
    for name, lat, lon in zip(location_df["Building Name"], location_df["lat"], location_df["lon"]):
        building = pygame.Rect(lat-BUILDING_WIDTH_HALF, lon-BUILDING_WIDTH_HALF, BUILDING_WIDTH, BUILDING_WIDTH)
        pygame.draw.rect(surface, BUILDING_COLOUR, building)

def draw_students(surface, students, people_df, colour_flag):
    for lat, lon, within_hours, id in zip(students["lat"], students["lon"], students["within_hours"], students["Student ID"]):
        if not within_hours:
            colour = VIOLATION_COLOUR
            # print(id)
        else:
            colour = colour_code_students(id, people_df, colour_flag)
        pygame.draw.circle(surface, colour, (lat, lon), STUDENT_RADIUS)