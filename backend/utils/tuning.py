import optuna
from sklearn.metrics import mean_squared_error
from models.lstm import build_lstm_model
from models.mlp import build_mlp_model

def optimize_model(model_type, X_train, y_train, X_val, y_val):
    def objective(trial):
        batch_size = trial.suggest_categorical("batch_size", [16, 32, 64])
        units = trial.suggest_int("units", 32, 128)

        if model_type == "lstm":
            model = build_lstm_model(trial, X_train.shape[1:])
        else:
            model = build_mlp_model(trial, X_train.shape)

        model.fit(X_train, y_train, epochs=10, batch_size=batch_size, verbose=0)
        preds = model.predict(X_val).flatten()
        return mean_squared_error(y_val, preds)

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=10)
    return study.best_params
