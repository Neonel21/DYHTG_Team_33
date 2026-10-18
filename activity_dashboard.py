
####Initial import of tools

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.interpolate import make_interp_spline
import pandas as pd



#### Loading Data and Processing for readbility
#### Exact pathway to the file to bypass file location issues - change to generalise for reusability
df = pd.read_csv(r"C:\Users\15sai\OneDrive\Computer Science\Hackathon stuff\SAS hackathon\security_logs.csv")

def time_to_minutes(t_str):
    t_str = t_str.strip()
    return int(t_str[:2]) * 60 + int(t_str[2:])


df[['Start_Str', 'End_Str']] = df['Time'].str.split('-', expand=True)

df['Start_Min'] = df['Start_Str'].apply(time_to_minutes)

df['End_Min'] = df['End_Str'].apply(time_to_minutes)

df.loc[df['End_Min'] < df['Start_Min'], 'End_Min'] += 24 * 60

timeline = range(0, 1440, 60)
records = []
locations = df['Location'].unique()

for loc in locations:
    loc_df = df[df['Location'] == loc]
    for t in timeline:
        count = loc_df[(loc_df['Start_Min'] <= t) & (loc_df['End_Min'] >= t)].shape[0]
        hour = (t // 60) % 24
        records.append({
            'Location': loc, 
            'Time_Minutes': t, 
            'Time_Label': f"{hour:02d}:00", 
            'Count': count
        })

occupancy_df = pd.DataFrame(records)

#### Interface for dropdown selection of the building and its corresponding graph
#### Change size depending on how large/adjust the UI for individual preferences
root = tk.Tk()
root.title("Campus Building Occupancy Viewer")
root.geometry("400x200")

label = tk.Label(root, text="Select a Building:", font=("Arial", 12))
label.pack(pady=10)

building_var = tk.StringVar(root)
building_var.set(locations[0])

dropdown = ttk.Combobox(root, textvariable=building_var, values=list(locations), state="readonly", width=30)
dropdown.pack(pady=10)

def show_graph():
    selected_loc = building_var.get()
    
    popup = tk.Toplevel(root)
    popup.title(f"Occupancy Graph - {selected_loc}")
    popup.geometry("700x450")
    
    loc_data = occupancy_df[occupancy_df['Location'] == selected_loc]
    
    x = loc_data['Time_Minutes'].values
    y = loc_data['Count'].values
    
    #### Smmothing out graph - more user friendly and readable
    #### using new library scipy recommended by ai for smoothing out the graph
    

    if len(x) > 3:
        X_Y_Spline = make_interp_spline(x, y)
        X_smooth = np.linspace(x.min(), x.max(), 300)
        Y_smooth = X_Y_Spline(X_smooth)
        Y_smooth = np.clip(Y_smooth, 0, None)
    else:
        X_smooth, Y_smooth = x, y
        
    fig, ax = plt.subplots(figsize=(7, 4))
    
    #### Smooth lines and graph fill
    #### more appealing and user friendly visualisation of data


    ax.plot(X_smooth, Y_smooth, color="#1f77b4", linewidth=2.5)
    ax.fill_between(X_smooth, Y_smooth, color="#1f77b4", alpha=0.15)
    
    ax.set_title(f"Hourly Occupancy: {selected_loc}", fontsize=11, fontweight='bold', pad=10)
    ax.set_xlabel("Time", fontsize=9)
    ax.set_ylabel("People", fontsize=9)
    
    #### frequency of ticks
    ax.set_xticks(range(0, 1440, 180))
    ax.set_xticklabels([f"{(t//60)%24:02d}:00" for t in range(0, 1440, 180)])
    
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    fig.tight_layout()
    
    canvas = FigureCanvasTkAgg(fig, master=popup)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

btn = tk.Button(root, text="View Graph", command=show_graph, font=("Arial", 10), bg="lightblue")
btn.pack(pady=15)

#### Rinse and repeat for all the other locations and their respective data
root.mainloop()