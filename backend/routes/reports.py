from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
import os
# import sys # Removed sys import
from datetime import datetime
from ..utils.report_generation.pdf_generator import generate_pdf_report
from typing import Dict, Any

router = APIRouter()

@router.post("/generate")
async def generate_report(
    stock_data: Dict[str, Dict[str, Any]],
    analysis_results: Dict[str, Dict[str, Any]],
    llm_recommendations: Dict[str, Dict[str, Any]]
):
    """
    Generate a PDF report for stock analysis
    
    Parameters:
    - stock_data: Dictionary containing historical stock data
    - analysis_results: Dictionary containing analysis metrics and forecasts
    - llm_recommendations: Dictionary containing LLM-generated recommendations
    """
    try:
        # Create reports directory if it doesn't exist
        os.makedirs("reports", exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stock_analysis_report_{timestamp}.pdf"
        output_path = os.path.join("reports", filename)
        
        # Combine data into a single dictionary
        report_data_for_pdf_generation = {
            "stock_data": stock_data,
            "analysis_results": analysis_results,
            "llm_recommendations": llm_recommendations
        }
        
        # sys.stdout.write(f"STDOUT_WRITE DEBUG: In routes/reports.py, data for PDF: {report_data_for_pdf_generation}\\n") # Removed debug
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
