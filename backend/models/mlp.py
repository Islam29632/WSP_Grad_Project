from keras.models import Sequential
from keras.layers import Input, Dense


def build_mlp_model(trial, input_shape, params=None):
    model = Sequential()
    model.add(Input(shape=(input_shape[1],)))  # Ensure input shape is correct

    # Get units from params or Optuna trial
    units = params["units"] if params else trial.suggest_int("units", 32, 128)

    model.add(Dense(units=units, activation="relu"))
    model.add(Dense(1))  # Output layer

    return model
