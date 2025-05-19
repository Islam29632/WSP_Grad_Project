import json
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
from datetime import datetime
import pandas as pd
import numpy as np

class StockReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        # Page for title and first chart will be added in a dedicated method or by generate_pdf_report

    def add_title_page_and_raw_price_chart(self, report_data):
        self.add_page()
        self.set_font("Arial", "B", 24)
        self.cell(0, 20, "Stock Analysis Report", ln=True, align="C")
        self.set_font("Arial", "", 12)
        self.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="R")
        self.ln(5) # Space before chart

        user_symbols = report_data.get("user_symbols", [])
        raw_price_data = report_data.get("raw_price_data", [])
        
        self.set_font("Arial", "B", 16) # Title for the chart on the first page
        self.cell(0, 10, "Raw Price Data Overview", ln=True, align="L")
        self.set_font("Arial", "", 12)

        chart_buffer_raw = self.generate_raw_price_chart(raw_price_data, user_symbols)
        if chart_buffer_raw:
            image_width = self.w - self.l_margin - self.r_margin
            # Calculate available height or set a max height for the first page chart
            current_y = self.get_y()
            available_height = self.h - current_y - self.b_margin - 10 # 10 for some padding
            
            # Get image dimensions (fpdf doesn't do this directly for BytesIO, so we might need to be careful or set a fixed aspect ratio)
            # For simplicity, let's assume a reasonable height or let fpdf scale width-wise.
            # If image is too tall, it might overflow or push content off.
            # A fixed height might be safer if aspect ratios vary wildly.
            img_h = image_width / (10/6) # Assuming approx 10:6 aspect ratio from figsize
            if img_h > available_height:
                img_h = available_height

            self.image(chart_buffer_raw, x=self.l_margin, w=image_width) # Let fpdf handle height based on width
        else:
            self.multi_cell(0, 10, "No raw price data available for selected symbols or chart generation failed.")
        self.ln(5)


    def generate_raw_price_chart(self, raw_price_data, user_symbols):
        if not raw_price_data or not user_symbols:
            return None

        try:
            df_raw = pd.DataFrame(raw_price_data)
            if "Ticker" not in df_raw.columns:
                print("Error: 'Ticker' column not found in raw_price_data for chart generation.")
                return None
            
            df_raw_filtered = df_raw[df_raw["Ticker"].isin(user_symbols)]
            if df_raw_filtered.empty:
                print(f"No raw price data for symbols: {user_symbols} after filtering.")
                return None
            
            # Ensure 'Date' column exists before trying to convert
            if "Date" not in df_raw_filtered.columns:
                print("Error: 'Date' column not found in filtered raw_price_data.")
                return None
            df_raw_filtered = df_raw_filtered.copy() # Avoid SettingWithCopyWarning
            df_raw_filtered.loc[:, "Date"] = pd.to_datetime(df_raw_filtered["Date"])

            fig, ax = plt.subplots(figsize=(10, 5)) # Adjusted figsize for potentially less space on title page
            for ticker in df_raw_filtered["Ticker"].unique():
                df_ticker = df_raw_filtered[df_raw_filtered["Ticker"] == ticker]
                ax.plot(df_ticker["Date"], df_ticker["Close"], label=ticker)

            ax.set_title(f"Raw Price Data for {', '.join(user_symbols)}")
            ax.set_xlabel("Date")
            ax.set_ylabel("Close Price")
            ax.legend()
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig) # Close the figure to free memory
            return buf
        except Exception as e:
            print(f"Error generating raw price chart: {e}") # Use print for backend logs
            return None

    def generate_ticker_analysis_chart(self, ticker_analysis_data, user_symbols):
        if not ticker_analysis_data or not user_symbols:
            return None

        try:
            plot_data = []
            # Filter ticker_analysis_data for user_symbols
            filtered_ticker_analysis = {k: v for k, v in ticker_analysis_data.items() if k in user_symbols}
            if not filtered_ticker_analysis:
                return None

            for ticker, data in filtered_ticker_analysis.items():
                if data.get("highest_price") is not None:
                    plot_data.append({"Ticker": ticker, "Metric": "Highest Price", "Value": data["highest_price"]})
                if data.get("lowest_price") is not None:
                    plot_data.append({"Ticker": ticker, "Metric": "Lowest Price", "Value": data["lowest_price"]})
                if data.get("growth_2020_percent") is not None:
                    plot_data.append({"Ticker": ticker, "Metric": "Growth Percentage", "Value": data["growth_2020_percent"]})

            if not plot_data:
                return None

            df_analysis = pd.DataFrame(plot_data)
            
            # Ensure 'Ticker' column exists and is not empty for x-axis labels
            unique_tickers_for_plot = df_analysis["Ticker"].unique()
            if len(unique_tickers_for_plot) == 0:
                return None


            fig, ax = plt.subplots(figsize=(10, 6))
            metrics = df_analysis["Metric"].unique()
            x = np.arange(len(unique_tickers_for_plot)) # Use unique_tickers_for_plot
            width = 0.25

            for i, metric in enumerate(metrics):
                metric_data = df_analysis[df_analysis["Metric"] == metric]
                # Align values with unique_tickers_for_plot
                values = []
                for t_plot in unique_tickers_for_plot:
                    val_series = metric_data[metric_data["Ticker"] == t_plot]["Value"]
                    values.append(val_series.iloc[0] if not val_series.empty else 0)
                ax.bar(x + i*width, values, width, label=metric)

            ax.set_ylabel("Value")
            ax.set_title(f"Ticker Price and Growth Analysis for {', '.join(user_symbols)}")
            ax.set_xticks(x + width/2 * (len(metrics) - 1))
            ax.set_xticklabels(unique_tickers_for_plot) # Use unique_tickers_for_plot
            ax.legend()
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig) # Close the figure to free memory
            return buf
        except Exception as e:
            print(f"Error generating ticker analysis chart: {e}") # Use print for backend logs
            return None


    def add_report_content(self, report_data):
        user_symbols = report_data.get("user_symbols", [])
        # Raw Price Data chart is now on the title page.

        # Add Ticker Analysis Chart (on a new page)
        self.add_page()
        self.set_x(self.l_margin)
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Ticker Price and Growth Analysis", ln=True, align="L")
        self.set_font("Arial", "", 12)
        ticker_analysis_data = report_data.get("ticker_analysis", {})
        chart_buffer_analysis = self.generate_ticker_analysis_chart(ticker_analysis_data, user_symbols)
        if chart_buffer_analysis:
            image_width = self.w - self.l_margin - self.r_margin
            self.image(chart_buffer_analysis, x=self.l_margin, w=image_width)
        else:
            self.multi_cell(0, 10, "No ticker analysis data available for selected symbols or chart generation failed.")
        self.ln(10)

        # Removed "Stock Data (Research)" section
        # Removed "Detailed Analysis Results" section

        # Add LLM Recommendations (filtered by user_symbols, on a new page)
        self.add_page()
        self.set_x(self.l_margin)
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "LLM Recommendations", ln=True, align="L")
        self.set_font("Arial", "", 12)
        llm_recommendations = report_data.get("llm_recommendations", {})
        filtered_llm_recommendations = {k: v for k, v in llm_recommendations.items() if k in user_symbols} if user_symbols else llm_recommendations
        
        if filtered_llm_recommendations:
            for ticker, rec_data in filtered_llm_recommendations.items():
                self.set_x(self.l_margin) 
                self.set_font("Arial", "B", 14)
                self.cell(0, 10, f"Ticker: {ticker}", ln=True)
                self.set_font("Arial", "", 12)
                self.set_x(self.l_margin) # Reset X
                self.multi_cell(0, 8, f"Recommendation: {rec_data.get('recommendation', 'N/A')}")
                self.set_x(self.l_margin) # Reset X
                self.multi_cell(0, 8, f"Reasoning: {rec_data.get('reasoning', 'No reasoning provided.')}")
                forecast = rec_data.get('forecast', {})
                if forecast:
                    self.set_x(self.l_margin) # Reset X
                    self.set_font("Arial", "U", 12)
                    self.cell(0, 8, "Forecasts:", ln=True)
                    self.set_font("Arial", "", 12)
                    if isinstance(forecast, dict):
                        for model, data in forecast.items():
                            self.set_x(self.l_margin) # Reset X
                            self.multi_cell(0, 8, f"- {model}: {data}")
                    else:
                        self.set_x(self.l_margin) # Reset X
                        self.multi_cell(0, 8, f"- Details: {forecast}")
                self.ln(5)
            self.ln(10)
        else:
            self.set_x(self.l_margin) # Reset X
            self.multi_cell(0, 10, "No LLM recommendations available.")
            self.ln(10)


def generate_pdf_report(report_data):
    pdf = StockReportPDF()
    pdf.add_title_page_and_raw_price_chart(report_data) # Add title page with first chart
    pdf.add_report_content(report_data) # Add subsequent content
    return pdf.output(dest='S') # Return PDF as bytes
