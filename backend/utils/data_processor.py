import os
import json
import pandas as pd
import numpy as np
import optuna
from sklearn.metrics import mean_squared_error
from utils.tuning import optimize_model
from utils.sequence_generator import generate_sequences
from models.lstm import build_lstm_model
from models.mlp import build_mlp_model
from utils.cache_utils import load_cached_params, save_cached_params


def get_actual_close_price(ticker, target_month="2025-01"):

    df = pd.read_csv("data/processed/cleaned_stock_data.csv")
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df[(df["ticker"] == ticker) & (df["date"].dt.strftime("%Y-%m") == target_month)]
    if df.empty:
        return None, None
    last_row = df.sort_values("date").iloc[-1]
    return float(last_row["close"]), str(last_row["date"].date())


def train_and_forecast(tickers=None, target_date="2025-01-31"):
    if tickers is None:
        tickers = ["AAPL", "MSFT"]

    final_results = {}
    param_cache = load_cached_params()

    for ticker in tickers:
        print(f"Processing {ticker}...")

        try:
            actual_price, used_date = get_actual_close_price(ticker, target_month="2025-01")
            if actual_price is None:
                print(f"No actual price found for {ticker} in January 2025, skipping.")
                continue

            # Generate sequences
            X_train_lstm, _, y_train, _, lstm_scaler= generate_sequences(ticker=ticker, model_type="lstm", forecast_target_date=target_date)
            X_train_mlp, _, _, _, mlp_scaler= generate_sequences(ticker=ticker, model_type="mlp", forecast_target_date=target_date)

            lstm_input_shape = X_train_lstm.shape[1:]
            mlp_input_shape = X_train_mlp.shape

            # LSTM tuning
            if ticker in param_cache and "lstm" in param_cache[ticker]:
                lstm_best_params = param_cache[ticker]["lstm"]
                print(f"Loaded cached LSTM params for {ticker}")
            else:
                lstm_best_params = optimize_model("lstm", X_train_lstm, y_train, X_train_lstm, y_train)
                lstm_best_params = {k: int(v) for k, v in lstm_best_params.items()}
                param_cache.setdefault(ticker, {})["lstm"] = lstm_best_params

            lstm_model = build_lstm_model(optuna.trial.FixedTrial(lstm_best_params), lstm_input_shape)
            lstm_model.fit(X_train_lstm, y_train, epochs=20, batch_size=lstm_best_params["batch_size"], verbose=0)


            # LSTM Forecast
            scaled_pred = lstm_model.predict(X_train_lstm[-1:]).flatten()[0]
            lstm_forecast = float(lstm_scaler.inverse_transform([[scaled_pred, 0, 0, 0, 0]])[0][0])
            lstm_mse = (lstm_forecast - actual_price) ** 2
            lstm_rmse = np.sqrt(lstm_mse)

            lstm_mse = (lstm_forecast - actual_price) ** 2
            lstm_rmse = np.sqrt(lstm_mse)

            # MLP tuning
            if ticker in param_cache and "mlp" in param_cache[ticker]:
                mlp_best_params = param_cache[ticker]["mlp"]
                print(f"Loaded cached MLP params for {ticker}")
            else:
                mlp_best_params = optimize_model("mlp", X_train_mlp, y_train, X_train_mlp, y_train)
                mlp_best_params = {k: int(v) for k, v in mlp_best_params.items()}
                param_cache.setdefault(ticker, {})["mlp"] = mlp_best_params

            mlp_model = build_mlp_model(optuna.trial.FixedTrial(mlp_best_params), mlp_input_shape)
            mlp_model.fit(X_train_mlp, y_train, epochs=20, batch_size=mlp_best_params["batch_size"], verbose=0)
            scaled_pred = mlp_model.predict(X_train_mlp[-1:]).flatten()[0]
            mlp_forecast = float(mlp_scaler.inverse_transform([[scaled_pred, 0, 0, 0, 0]])[0][0])

            mlp_mse = (mlp_forecast - actual_price) ** 2
            mlp_rmse = np.sqrt(mlp_mse)

            final_results[ticker] = {
                "target_date": target_date,
                "actual_price": actual_price,
                "LSTM": {
                    "forecast": lstm_forecast,
                    "mse": lstm_mse,
                    "rmse": lstm_rmse
                },
                "MLP": {
                    "forecast": mlp_forecast,
                    "mse": mlp_mse,
                    "rmse": mlp_rmse
                }
            }

        except Exception as e:
            print(f"⚠️ Skipping {ticker} due to error: {e}")

    save_cached_params(param_cache)

    with open("outputs/forecast_results.json", "w") as f:
        json.dump(final_results, f, indent=4)

    return final_results
