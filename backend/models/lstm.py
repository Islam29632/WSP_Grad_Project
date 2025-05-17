from keras.models import Sequential
from keras.layers import Input, LSTM, Dense

def build_lstm_model(lstm_best, input_shape):
    model = Sequential()
    model.add(Input(shape=input_shape))  
    model.add(LSTM(units=lstm_best['units']))
    model.add(Dense(1))
    return model
