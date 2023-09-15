import pandas as pd
import numpy as np

def parking_score(df, duration_scale=1.1, noise_scale=1.3, leisure_scale=1, traffic_scale=1):

    score = []

    for index, row in df.iterrows():

        duration = 1/row['duration_norm']
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
