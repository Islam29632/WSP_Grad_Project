import pathlib
import sys
import os
import json
from datetime import datetime
from numbers import Number
import numpy as np
import pandas as pd
from tensorflow.keras.optimizers import Adam, RMSprop

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BASE_DIR))

from backend.utils.tuning import optimize_model
from backend.utils.sequence_generator import generate_sequences
from backend.models.lstm import build_lstm_model
from backend.models.mlp import build_mlp_model
from backend.utils.cache_utils import load_cached_params, save_cached_params


def inverse_scale_close_only(scaler, scaled_close):
    """
    Inverse-transform just the “close” column (assumed to be the first feature).
    """
    dummy = np.zeros((1, scaler.mean_.shape[0]))
    dummy[0, 0] = scaled_close
    return scaler.inverse_transform(dummy)[0][0]


def get_first_trading_day_and_price(ticker, target_month="2025-01"):
    """
    Return (<first_date>, <close_price>) for the *earliest* trading day in
    `target_month` for `ticker`. If none exists, returns (None, None).
    """
    
    #data_file = BASE_DIR / "data" / "processed" / "cleaned_stock_data.csv"
    
    #if not data_file.exists():
        #raise FileNotFoundError(f"Required data file not found: {data_file}")
        
    #df = pd.read_csv(data_file)

    df = pd.read_csv("../backend/data/processed/cleaned_stock_data.csv")
    
    df["date"] = pd.to_datetime(df["date"], utc=True)

    month_df = df[
        (df["ticker"] == ticker)
        & (df["date"].dt.strftime("%Y-%m") == target_month)
    ]

    if month_df.empty:
        return None, None

    first_row = month_df.sort_values("date").iloc[0]
    first_date = str(first_row["date"].date())   # 'YYYY-MM-DD'
    first_close = float(first_row["close"])
    return first_date, first_close


def train_and_forecast(tickers=None, target_month="2025-01"):
    """
    For each ticker, find the first trading day in `target_month`,
    train LSTM & MLP up to *but not including* that day, then forecast it.
    """
    
    if tickers is None:
        tickers = ["AAPL", "MSFT"]

    final_results = {}
    param_cache = load_cached_params()

    for ticker in tickers:
        print(f"Processing {ticker}...")

        # ---- NEW: dynamically choose the first available date in the month
        target_date, actual_price = get_first_trading_day_and_price(
            ticker, target_month=target_month
        )
        if actual_price is None:
            print(f"No price found for {ticker} in {target_month}, skipping.")
            continue

        print(f"   • forecasting {target_date}")

        try:

            X_lstm, _, y_train, _, lstm_scaler = generate_sequences(
                ticker=ticker,
                model_type="lstm",
                forecast_target_date=target_date
            )
            X_mlp, _, _, _, mlp_scaler = generate_sequences(
                ticker=ticker,
                model_type="mlp",
                forecast_target_date=target_date
            )

            lstm_input_shape = X_lstm.shape[1:]
            mlp_input_shape = X_mlp.shape


            if ticker in param_cache and "lstm" in param_cache[ticker]:
                lstm_best = param_cache[ticker]["lstm"]
                print("      ↳ loaded cached LSTM params")
            else:
                lstm_best = optimize_model(
                    "lstm", X_lstm, y_train, X_lstm, y_train
                )
                param_cache.setdefault(ticker, {})["lstm"] = lstm_best

            lstm_best = {
                k: int(v) if isinstance(v, Number) and not isinstance(v, bool) else v
                for k, v in lstm_best.items()
            }
            lstm_opt = Adam() if lstm_best["optimizer"] == "adam" else RMSprop()

            lstm_model = build_lstm_model(
                None, lstm_input_shape, lstm_best
            )
            lstm_model.compile(optimizer=lstm_opt, loss="mse")
            lstm_model.fit(
                X_lstm,
                y_train,
                epochs=10,
                batch_size=lstm_best["batch_size"],
                verbose=0
            )

            lstm_scaled_pred = lstm_model.predict(X_lstm[-1:]).flatten()[0]
            lstm_forecast = float(
                inverse_scale_close_only(lstm_scaler, lstm_scaled_pred)
            )
            lstm_mse = (lstm_forecast - actual_price) ** 2
            lstm_rmse = np.sqrt(lstm_mse)


            if ticker in param_cache and "mlp" in param_cache[ticker]:
                mlp_best = param_cache[ticker]["mlp"]
                print("      ↳ loaded cached MLP params")
            else:
                mlp_best = optimize_model(
                    "mlp", X_mlp, y_train, X_mlp, y_train
                )
                param_cache.setdefault(ticker, {})["mlp"] = mlp_best

            mlp_best = {
                k: int(v) if isinstance(v, Number) and not isinstance(v, bool) else v
                for k, v in mlp_best.items()
            }
            mlp_opt = Adam() if mlp_best["optimizer"] == "adam" else RMSprop()

            mlp_model = build_mlp_model(
                None, mlp_input_shape, mlp_best
            )
            mlp_model.compile(optimizer=mlp_opt, loss="mse")
            mlp_model.fit(
                X_mlp,
                y_train,
                epochs=10,
                batch_size=mlp_best["batch_size"],
                verbose=0
            )

            mlp_scaled_pred = mlp_model.predict(X_mlp[-1:]).flatten()[0]
            mlp_forecast = float(
                inverse_scale_close_only(mlp_scaler, mlp_scaled_pred)
            )
            mlp_mse = (mlp_forecast - actual_price) ** 2
            mlp_rmse = np.sqrt(mlp_mse)


            final_results[ticker] = {
                "target_date": target_date,
                "actual_price": actual_price,
                "LSTM": {
                    "forecast": lstm_forecast,
                    "mse": lstm_mse,
                    "rmse": lstm_rmse,
                },
                "MLP": {
                    "forecast": mlp_forecast,
                    "mse": mlp_mse,
                    "rmse": mlp_rmse,
                },
            }

        except Exception as e:
            print(f"Skipping {ticker} due to error: {e}")


    save_cached_params(param_cache)

    os.makedirs("../backend/outputs", exist_ok=True)
    out_file = f"../backend/outputs/forecast_results.json"
    with open(out_file, "w") as f:
        json.dump(final_results, f, indent=4)

    print(f"\nResults saved to {out_file}")
    return final_results
