from fpdf import FPDF
import matplotlib.pyplot as plt
import io
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
        
    def add_section_header(self, title):
        """Add a section header to the PDF"""
        self.set_font("Arial", "B", 16)
        self.ln(10)
        self.cell(0, 10, title, ln=True)
        self.set_font("Arial", "", 12)
        self.ln(5)

    def add_table(self, headers, data):
        """Add a table to the PDF"""
        # Calculate column width
        col_width = self.get_string_width(max(headers, key=len)) + 10
        line_height = 10

        # Headers
        self.set_font("Arial", "B", 12)
        for header in headers:
            self.cell(col_width, line_height, header, border=1)
        self.ln()

        # Data
        self.set_font("Arial", "", 12)
        for row in data:
            for item in row:
                self.cell(col_width, line_height, str(item), border=1)
            self.ln()
        self.ln(5)

    def add_plot(self, figure):
        """Add a matplotlib figure to the PDF"""
        buf = io.BytesIO()
        figure.savefig(buf, format='png', bbox_inches='tight')
        self.image(buf, x=10, w=190)
        buf.close()
        plt.close(figure)
        self.ln(5)

    def add_text_section(self, title, content):
        """Add a text section with title and content"""
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, title, ln=True)
        self.set_font("Arial", "", 12)
        self.multi_cell(0, 10, content)
        self.ln(5)

def generate_stock_report(stock_data, analysis_results, llm_recommendations):
    """
    Generate a PDF report for stock analysis
    
    Parameters:
    - stock_data: Dictionary containing historical stock data
    - analysis_results: Dictionary containing analysis metrics and forecasts
    - llm_recommendations: Dictionary containing LLM-generated recommendations
    """
    pdf = StockReportPDF()
    
    # Add Stock Overview Section
    for symbol in stock_data:
        pdf.add_section_header(f"Stock Analysis: {symbol}")
        
        # Basic Statistics Table
        if "basic_stats" in analysis_results[symbol]:
            stats = analysis_results[symbol]["basic_stats"]
            pdf.add_text_section("Basic Statistics", "")
            headers = ["Metric", "Value"]
            data = [
                ["Average Price", f"${stats['average_price']:.2f}"],
                ["Maximum Price", f"${stats['max_price']:.2f}"],
                ["Minimum Price", f"${stats['min_price']:.2f}"]
            ]
            pdf.add_table(headers, data)

        # Price History Plot
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            dates = list(stock_data[symbol].keys())
            prices = list(stock_data[symbol].values())
            ax.plot(dates, prices)
            ax.set_title(f"{symbol} Price History")
            ax.set_xlabel("Date")
            ax.set_ylabel("Price ($)")
            plt.xticks(rotation=45)
            plt.tight_layout()
            pdf.add_plot(fig)
        except Exception as e:
            pdf.cell(0, 10, f"Error generating plot: {str(e)}", ln=True)

        # Forecast Section
        if "forecast_next_month" in analysis_results[symbol]:
            pdf.add_text_section("Price Forecast", 
                f"Forecasted price for next month: ${analysis_results[symbol]['forecast_next_month']:.2f}")

        # Error Metrics
        if "error_metrics" in analysis_results[symbol]:
            metrics = analysis_results[symbol]["error_metrics"]
            pdf.add_text_section("Forecast Error Metrics", "")
            headers = ["Metric", "Value"]
            data = [
                ["MSE", f"{metrics.get('mse', 'N/A'):.4f}"],
                ["RMSE", f"{metrics.get('rmse', 'N/A'):.4f}"]
            ]
            pdf.add_table(headers, data)

        # LLM Recommendations
        if symbol in llm_recommendations:
            pdf.add_text_section("AI-Generated Recommendations", 
                llm_recommendations[symbol]["llm_advice"])

        # Rule-based Recommendations
        if "rule_based" in llm_recommendations[symbol]:
            pdf.add_text_section("Rule-Based Analysis", 
                "\n".join([f"• {rule}" for rule in llm_recommendations[symbol]["rule_based"]]))

        pdf.add_page()

    return pdf

def save_stock_report(stock_data, analysis_results, llm_recommendations, output_path):
    """
    Generate and save a stock analysis report as PDF
    
    Parameters:
    - stock_data: Dictionary containing historical stock data
    - analysis_results: Dictionary containing analysis metrics and forecasts
    - llm_recommendations: Dictionary containing LLM-generated recommendations
    - output_path: Path where the PDF should be saved
    """
    pdf = generate_stock_report(stock_data, analysis_results, llm_recommendations)
    pdf.output(output_path)
