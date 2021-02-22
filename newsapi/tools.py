import pandas as pd

def aggregate(df_list):
    if (len(df_list) == 0):
        return "{}"
    df = pd.concat(df_list, ignore_index=True, axis=0)
    df["certainty_num"]=100
    df['label'] = False
    data = df.to_json(orient="records")
    return data