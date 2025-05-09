from keras.models import Sequential
from keras.layers import Input, LSTM, Dense

def build_lstm_model(trial, input_shape):
    model = Sequential()
    model.add(Input(shape=input_shape))  
    model.add(LSTM(units=trial.suggest_int("units", 32, 128)))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mse")
    return model
