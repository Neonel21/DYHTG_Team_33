from config import BUILDING_WIDTH_HALF

def clicked_on_building(mouse_pos, buildings):
    for building in buildings:
        x = mouse_pos[0]
        y = mouse_pos[1]
        lat = building[1]
        lon = building[2]
        if (x >= lat-BUILDING_WIDTH_HALF and x <= lat+BUILDING_WIDTH_HALF
            and y >= lon-BUILDING_WIDTH_HALF and y <= lon+BUILDING_WIDTH_HALF):
            return building
    return None

def building_after_click(pos, buildings, selected, popup_rect, close_rect):
    if selected is None:
        hit = clicked_on_building(pos, buildings)
        return hit[0] if hit else None

    if close_rect and close_rect.collidepoint(pos):
        return None

    if popup_rect and popup_rect.collidepoint(pos):
        return selected

    hit = clicked_on_building(pos, buildings)
    return hit[0] if hit else None