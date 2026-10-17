import pygame
import pandas as pd

width, height = 700, 700

location_df = pd.read_csv("location_data.csv")
coords = location_df["Geolocation"].str.strip("{}").str.split(expand=True).astype(float)
location_df[["lat", "lon"]] = coords

average_location = location_df[["lat", "lon"]].mean()
min_lat, min_lon = (location_df["lat"].min(), location_df["lon"].min())
max_lat, max_lon = (location_df["lat"].max(), location_df["lon"].max())

lat_range = max_lat - min_lat
lon_range = max_lon - min_lon

location_df["lat"] = (location_df["lat"] - min_lat)/(max_lat - min_lat)*(width-100)+50
location_df["lon"] = (location_df["lon"] - min_lon)/(max_lon - min_lon)*(height-100)+50

print(location_df["lat"], location_df["lon"])

people_df = pd.read_csv("people_data.csv")

security_logs_df = pd.read_csv("security_logs.csv")

# pygame.init()

# canvas = pygame.display.set_mode((width, height))

# pygame.display.set_caption("My Board")
# exit = False

# while not exit:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             exit = True
#     pygame.display.update()