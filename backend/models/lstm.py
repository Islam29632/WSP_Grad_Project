from keras.models import Sequential
from keras.layers import Input, LSTM, Dense


def build_lstm_model(trial, input_shape, params=None):
    model = Sequential()
    model.add(Input(shape=input_shape))

    # Use passed-in params or fall back to Optuna trial (for tuning mode)
    units = params["units"] if params else trial.suggest_int("units", 32, 128)

    model.add(LSTM(units=units))
    model.add(Dense(1))  # Output layer

    return model

