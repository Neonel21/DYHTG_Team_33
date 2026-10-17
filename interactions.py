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