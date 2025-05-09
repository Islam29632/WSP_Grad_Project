from keras.models import Sequential
from keras.layers import Input, Dense


def build_mlp_model(trial, input_shape):
    model = Sequential()
    model.add(Input(shape=(input_shape[1],)))  
    model.add(Dense(units=trial.suggest_int("units", 32, 128), activation="relu"))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mse")
    return model
