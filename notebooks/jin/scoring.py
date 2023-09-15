import pandas as pd
import numpy as np

# df_ = pd.read_csv("./data/processed/full_final_df_norm.csv")

def parking_score(df, duration_scale=1.1, noise_scale=1, leisure_scale=1, traffic_scale=1):

    score = []

    for index, row in df.iterrows():

        duration = 1/row['parking_duration']
        noise = 1/row['noise_norm']
        leisure = 1/row['leisure_norm']
        traffic = 1/row['traffic_norm']

        sum_ = np.sum(duration + noise + leisure + traffic)
        score.append(((duration_scale * duration) + (noise_scale * noise) + (leisure_scale * leisure) + (traffic_scale * traffic))/(sum_))
    
    min_val = np.min(score)
    max_val = np.max(score)

    normalized_data = (score - min_val) / (max_val - min_val)

    df['score'] = normalized_data
    return df

# parking_score(df_[0:12])
