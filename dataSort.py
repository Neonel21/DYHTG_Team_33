#imports
import pandas as pd
import ast

selected = []

# Function to safely parse stringified lists/sets/nan into real lists
def parse_societies(val):
  if pd.isna(val) or str(val).strip() == "nan" or not str(val).strip():
    return []

  # Replace newlines with commas so Python can evaluate it properly
  cleaned = str(val).replace("\n", ",")

  try:
    # ast.literal_eval safely parses strings like "['A', 'B']" or "{'A', 'B'}"
    result = ast.literal_eval(cleaned)
    return list(result)  # Convert sets/lists to a standard list
  except (ValueError, SyntaxError):
    # Fallback if it's just a plain string
    return [str(val)]

# Reads the data
data = pd.read_csv("people_data.csv")

# Apply the parsing function to the column
data["Societies"] = data["Societies"].apply(parse_societies)

# Explode so each society gets its own row
df = data.explode("Societies")

# Clean up any leftover whitespace or quotes if needed
df["Societies"] = df["Societies"].str.strip().str.strip("'\"")

# Drop rows where societies are empty/NaN
df = df.dropna(subset=["Societies"])

def identifier(main,list):
    status_year = False
    status_sub = False
    status_soc = False

    if main == "year":
        main = "Year of Study"
        status_year = True
        year = input("year")
    elif main == "sub":
        main = "Subject"
        status_sub = True 
        sub = input("sub")
    elif main == "soc":
        main = "Societies"
        status_soc = True
        soc = input("soc")

    if status_year:
        for _, row in data.iterrows():
            if row[main] == int(year):
                list.append(row["Student ID"])
    if status_sub:
        for _, row in data.iterrows():
            if row[main] == str(sub):
                list.append(row["Student ID"])
    if status_soc:
        for _, row in df.iterrows():
            if row[main] == str(soc):
                list.append(row["Student ID"])

#tester
identifier("soc",selected)

#prints all in whatever you searched 
for i in range(len(selected)):
    print(selected[i])






