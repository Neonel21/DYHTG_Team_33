import pandas as pd
import ast

def parse_societies(val):
  if pd.isna(val) or str(val).strip() == "nan" or not str(val).strip():
    return []

  cleaned = str(val).replace("\n", ",")

  try:
    result = ast.literal_eval(cleaned)
    return list(result)
  except (ValueError, SyntaxError):
    return [str(val)]

def read_societies(data):
    data["Societies"] = data["Societies"].apply(parse_societies)

    df = data.explode("Societies")

    df["Societies"] = df["Societies"].str.strip().str.strip("'\"")

    df = df.dropna(subset=["Societies"])

    return df

def identifier(main, data, value):
    list = []
    status_year = False
    status_sub = False
    status_soc = False

    if main == "year":
        main = "Year of Study"
        status_year = True
        year = value
    elif main == "sub":
        main = "Subject"
        status_sub = True 
        sub = value
    elif main == "soc":
        df = read_societies(data)
        main = "Societies"
        status_soc = True
        soc = value

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
