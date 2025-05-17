from keras.models import Sequential
from keras.layers import Input, Dense


def build_mlp_model(mlp_best, input_shape):
    model = Sequential()
    model.add(Input(shape=(input_shape[1],)))  
    model.add(Dense(units=mlp_best['units'], activation="relu"))
    model.add(Dense(1))
    return model
