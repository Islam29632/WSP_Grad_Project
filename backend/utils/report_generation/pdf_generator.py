import json
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
# import sys # Removed sys import
from datetime import datetime

class StockReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_font("Arial", "B", 24)
        self.cell(0, 20, "Stock Analysis Report", ln=True, align="C")
        self.set_font("Arial", "", 12)
        self.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="R")
        
    def add_report_content(self, report_data):
        self.ln(10) # Add some space after the header

        # Add Stock Data (Research)
        self.set_x(self.l_margin) # Reset X to left margin
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Stock Data (Research)", ln=True, align="L")
        self.set_font("Arial", "", 12)
        stock_data = report_data.get("stock_data", {})
        if stock_data:
            for ticker, data in stock_data.items():
                self.set_x(self.l_margin) # Reset X
                self.set_font("Arial", "B", 14)
                self.cell(0, 10, f"Ticker: {ticker}", ln=True)
                self.set_font("Arial", "", 12)
                if isinstance(data, dict):
                    for key, value in data.items():
                        self.set_x(self.l_margin) # Reset X
                        self.multi_cell(0, 8, f"{key}: {value}")
                else:
                    self.set_x(self.l_margin) # Reset X
                    self.multi_cell(0, 8, str(data))
                self.ln(5)
        else:
            self.set_x(self.l_margin) # Reset X
            self.multi_cell(0, 10, "No stock data available.")
        self.ln(10)

        # Add Analysis Results
        self.set_x(self.l_margin) # Reset X to left margin
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Analysis Results", ln=True, align="L")
        self.set_font("Arial", "", 12)
        analysis_results = report_data.get("analysis_results", {})
        if analysis_results:
            for ticker, data in analysis_results.items():
                self.set_x(self.l_margin) # Reset X
                self.set_font("Arial", "B", 14)
                self.cell(0, 10, f"Ticker: {ticker}", ln=True)
                self.set_font("Arial", "", 12)
                if isinstance(data, dict):
                    for key, value in data.items():
                        self.set_x(self.l_margin) # Reset X
                        self.multi_cell(0, 8, f"{key}: {value}")
                else:
                    self.set_x(self.l_margin) # Reset X
                    self.multi_cell(0, 8, str(data))
                self.ln(5)
        else:
            self.set_x(self.l_margin) # Reset X
            self.multi_cell(0, 10, "No analysis results available.")
        self.ln(10)

        # Add LLM Recommendations
        self.set_x(self.l_margin) # Reset X to left margin
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "LLM Recommendations", ln=True, align="L")
        self.set_font("Arial", "", 12)
        llm_recommendations = report_data.get("llm_recommendations", {})
        if llm_recommendations:
            for ticker, rec_data in llm_recommendations.items():
                self.set_x(self.l_margin) # Reset X
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
        else:
            self.set_x(self.l_margin) # Reset X
            self.multi_cell(0, 10, "No LLM recommendations available.")
        self.ln(10)

def generate_pdf_report(report_data):
    # sys.stdout.write(f"STDOUT_WRITE DEBUG: In pdf_generator.py, received: {report_data}\\n") # Removed debug
    # sys.stdout.flush() # Removed debug
    pdf = StockReportPDF()
    pdf.add_report_content(report_data)
    return pdf.output(dest='S') # Return PDF as bytes
