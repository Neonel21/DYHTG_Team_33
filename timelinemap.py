import pygame
import pandas as pd

width, height = 700, 700
building_colour = (255, 255, 255)
building_width = 30
building_width_half = building_width/2

def normalise_lat_lon(location_df):
    min_lat, min_lon = (location_df["lat"].min(), location_df["lon"].min())
    max_lat, max_lon = (location_df["lat"].max(), location_df["lon"].max())

    location_df["lat"] = (location_df["lat"] - min_lat)/(max_lat - min_lat)*(width-100)+50
    location_df["lon"] = (location_df["lon"] - min_lon)/(max_lon - min_lon)*(height-100)+50
    return location_df

def drawBuildings(location_df):
    for name, lat, lon in zip(location_df["Building Name"], location_df["lat"], location_df["lon"]):
        pygame.draw.rect(canvas, building_colour, pygame.Rect(lat-building_width_half, lon-building_width_half, building_width, building_width))

location_df = pd.read_csv("location_data.csv")

coords = location_df["Geolocation"].str.strip("{}").str.split(expand=True).astype(float)
location_df[["lat", "lon"]] = coords
location_df = normalise_lat_lon(location_df)

people_df = pd.read_csv("people_data.csv")

security_logs_df = pd.read_csv("security_logs.csv")

pygame.init()

canvas = pygame.display.set_mode((width, height))

pygame.display.set_caption("Map")
exit = False

while not exit:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit = True

    drawBuildings(location_df)
    pygame.display.update()