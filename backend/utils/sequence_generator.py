import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def generate_sequences(ticker, model_type, sequence_length=10, forecast_target_date=None):
    df = pd.read_csv("data/processed/cleaned_stock_data.csv")
    df = df[df['ticker'] == ticker].sort_values("date").reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'], utc=True)

    if forecast_target_date:
        df = df[df['date'] < pd.Timestamp(forecast_target_date, tz="UTC")]

    features = ['close', 'sma_5', 'sma_10', 'sma_21', 'std_5']
    df = df[features].dropna()


    scaler = StandardScaler()
    scaled = scaler.fit_transform(df)

    X, y = [], []
    for i in range(sequence_length, len(scaled)):
        X.append(scaled[i - sequence_length:i])
        y.append(scaled[i][0])

    X = np.array(X)
    y = np.array(y)
    if model_type == "mlp":
        X = X.reshape((X.shape[0], -1))

    return X, None, y, None, scaler
