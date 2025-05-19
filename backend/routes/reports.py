from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
import os
# import sys # Removed sys import
from datetime import datetime
from ..utils.report_generation.pdf_generator import generate_pdf_report
from typing import Dict, Any, List # Added List import

router = APIRouter()

@router.post("/generate")
async def generate_report(
    raw_price_data_payload: List[Dict[str, Any]],
    analysis_results_payload: Dict[str, Dict[str, Any]],
    llm_recommendations_payload: Dict[str, Dict[str, Any]],
    research_data_payload: Dict[str, Any], # Retained for now, though PDF won't use it
    user_symbols_payload: List[str], # Added to receive user-selected symbols
    forecast_vs_actual_payload: Dict[str, Any] # Added for forecast data
):
    """
    Generate a PDF report for stock analysis

    Parameters:
    - raw_price_data_payload: List of dictionaries containing raw historical stock data.
    - analysis_results_payload: Dictionary containing ticker-specific analysis metrics.
    - llm_recommendations_payload: Dictionary containing LLM-generated recommendations.
    - research_data_payload: Dictionary containing research data for stocks.
    - user_symbols_payload: List of user-selected stock symbols.
    - forecast_vs_actual_payload: Dictionary containing forecast vs. actual price data.
    """
    try:
        # Create reports directory if it doesn't exist
        os.makedirs("reports", exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stock_analysis_report_{timestamp}.pdf"
        output_path = os.path.join("reports", filename)

        # Combine data into a single dictionary for the PDF generator.
        # The PDF generator expects specific keys.
        report_data_for_pdf_generation = {
            "raw_price_data": raw_price_data_payload,
            "ticker_analysis": analysis_results_payload,
            # "stock_data": research_data_payload, # This section will be removed from PDF
            "analysis_results": analysis_results_payload,
            "llm_recommendations": llm_recommendations_payload,
            "user_symbols": user_symbols_payload, # Pass symbols to PDF generator
            "forecast_vs_actual": forecast_vs_actual_payload, # Pass forecast data
        }
        
        # sys.stdout.write(f"STDOUT_WRITE DEBUG: In routes/reports.py, data for PDF: {report_data_for_pdf_generation}\\n")
        # sys.stdout.flush() # Removed debug
        
        # Generate the report bytes
        pdf_bytes = generate_pdf_report(report_data_for_pdf_generation)
        
        # Save the report bytes to a file
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        
        # Return the PDF file
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        # sys.stderr.write(f"STDERR_WRITE ERROR in routes/reports.py: {str(e)}\\n") # Removed debug
        # sys.stderr.flush() # Removed debug
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_report(filename: str):
    """Download a previously generated report"""
    file_path = os.path.join("reports", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)
