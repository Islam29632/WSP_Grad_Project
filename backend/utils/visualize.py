def visualize_prices(self, ticker: dict[str, dict] = None) -> str:
        models = ["Actual", "LSTM", "MLP"]
        prices = [
            final_results["actual_price"],
            final_results["LSTM"]["forecast"],
            final_results["MLP"]["forecast"]
        ]

        plt.figure(figsize=(6, 4))
        plt.bar(models, prices, color=["gray", "skyblue", "orange"])
        plt.title(f"Forecast vs Actual on {final_results['target_date']}")
        plt.ylabel("Price")
        plt.grid(axis='y')
        plt.tight_layout()
        plt.show()

        # --- Plot 2: RMSE Comparison ---
        rmses = [
            final_results["LSTM"]["rmse"],
            final_results["MLP"]["rmse"]
        ]

        plt.figure(figsize=(6, 4))
        plt.bar(["LSTM RMSE", "MLP RMSE"], rmses, color=["skyblue", "orange"])
        plt.title("RMSE Comparison")
        plt.ylabel("RMSE")
        plt.grid(axis='y')
        plt.tight_layout()
        plt.show()
