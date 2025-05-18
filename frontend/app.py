import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests
from datetime import datetime
import time # Import time module
from auth import init_auth_state, login, signup
import subprocess
import os

# Page configuration
st.set_page_config(page_title="Stock Analysis App", layout="wide")

# Initialize session states
init_auth_state()
if "results" not in st.session_state:
    st.session_state.results = {"research": {}, "analysis": {}, "final": {}}
if "run_triggered" not in st.session_state:
    st.session_state.run_triggered = False
if "backend_output" not in st.session_state:
    st.session_state.backend_output = ""

# Handle authentication (Login Page)
if not st.session_state.get("authenticated", False):
    if st.session_state.get("show_signup", False):
        signup()
    else:
        login()
    st.stop() # Stop execution if not authenticated

# --- Main Application Content (after successful authentication) ---

st.title("Welcome to the Stock Analysis App")
st.markdown("""
This app fetches and analyzes stock data, providing trends, anomalies, and investment proposals. Navigate to the Analysis page to:

*   Enter stock symbols (e.g., AAPL).
*   Run the analysis.
*   View results and price forecasts.
""")

# Analysis Page
st.title("Stock Analysis")
st.markdown("Enter stock symbols and click 'Start Analysis Pipeline' to begin..")

# Inputs
default_symbols = "AAPL"
symbols_input = st.text_input(
"Stock Symbols (comma-separated)", default_symbols)
user_pov = "I’m a conservative investor looking for stable growth with low risk."

# Button to trigger backend execution
if st.button("Start Analysis Pipeline"):
    symbols = [symbol.strip() for symbol in symbols_input.split(',') if symbol.strip()]
    if symbols:
        st.session_state.run_triggered = True
        st.session_state.results = {"research": {}, "analysis": {}, "final": {}} # Clear previous results
        st.session_state.backend_output = "" # Clear previous backend output
        st.rerun() # Rerun to show progress indicators and start pipeline

# Run analysis pipeline if triggered
if st.session_state.run_triggered:
    symbols = [symbol.strip() for symbol in symbols_input.split(',') if symbol.strip()]
    if symbols:
        # Initialize progress bar and status text
        backend_output_area = st.empty() # Area to display backend output

        start_time_total = time.time() # Start timer for total duration
        try:
            # Use st.status for step-by-step feedback
            with st.status("Starting analysis pipeline...", expanded=True) as status:

                # Step 1: Run dataset update check script
                start_time_step1 = time.time() # Start timer for step 1
                dataset_script_path = "../backend/database/pipeline_dataset.py"
                # Removed capture_output=True and text=True to allow output to go to terminal
                subprocess.run(["python", dataset_script_path], check=True)
                # Removed code to append and display captured output
                duration_step1 = time.time() - start_time_step1 # Calculate duration for step 1
                st.success(f"Dataset check complete ({duration_step1:.2f}s). Now you have the last version") # Green feedback
                status.update(label="Dataset check complete", state="complete", expanded=True) # Keep default green status
                # Step 2: Run main agent call script
                start_time_step2 = time.time() # Start timer for step 2
                st.write("Running main agent call...")
                agent_script_path = "../backend/agent_main_call.py"
                # Pass symbols and user_pov as command-line arguments
                # Note: The backend script is expected to save the results to crew_result.json
                # Removed capture_output=True and text=True to allow output to go to terminal
                subprocess.run(["python", agent_script_path, "--symbols", ",".join(symbols), "--user_pov", user_pov], check=True)
                # Removed code to append and display captured output
                duration_step2 = time.time() - start_time_step2 # Calculate duration for step 2
                st.warning(f"Main agent call complete ({duration_step2:.2f}s).") # Orange feedback
                status.update(label="Main agent call complete", state="complete", expanded=True) # Keep default green status
                # Read the results from crew_result.json
                start_time_read = time.time() # Start timer for reading results
                st.write("Reading results...")
                results_file_path = "../backend/outputs/crew_result.json"
                if os.path.exists(results_file_path):
                    with open(results_file_path, "r") as f:
                        loaded_data = json.load(f)

                    # Ensure st.session_state.results is a dictionary
                    # and place loaded_data appropriately.
                    current_results_template = {"research": {}, "analysis": {}, "recommendations": [], "final": {}}
                    if isinstance(st.session_state.results, dict):
                        current_results_template.update(st.session_state.results)

                    if isinstance(loaded_data, list):
                        # If crew_result.json is just a list of recommendations
                        current_results_template["recommendations"] = loaded_data
                        st.session_state.results = current_results_template
                    elif isinstance(loaded_data, dict):
                        # If crew_result.json is a dict (hopefully with a "recommendations" key)
                        st.session_state.results = loaded_data
                    else:
                        st.warning(f"Unexpected data type loaded from {results_file_path}. Expected dict or list. Resetting results.")
                        st.session_state.results = {"research": {}, "analysis": {}, "final": {}} # Reset

                    duration_read = time.time() - start_time_read # Calculate duration for reading results
                    st.warning(f"Results read successfully ({duration_read:.2f}s).") # Orange feedback
                else:
                    duration_read = time.time() - start_time_read # Calculate duration even if file not found
                    st.warning(f"Results file not found at {results_file_path}. Cannot display results ({duration_read:.2f}s).") # Orange feedback
                    st.session_state.results = {"research": {}, "analysis": [], "recommendations": [], "final": {}} # Clear results if file not found

                # Final completion message for the overall status
                status.update(label="Analysis pipeline completed!", state="complete", expanded=True) # Keep expanded

            end_time_total = time.time() # End timer for total duration
            total_duration = end_time_total - start_time_total # Calculate total duration
            st.info(f"Total analysis time: {total_duration:.2f} seconds.") # Display total time

            st.success("Analysis pipeline completed! Results are displayed below.")
            st.session_state.run_triggered = False # Reset trigger after completion
        except FileNotFoundError as e:
            st.error(f"Error: Required file not found: {e}")
            st.session_state.backend_output += f"Error: Required file not found: {e}\n"
            backend_output_area.text_area("Backend Output", st.session_state.backend_output, height=300)
            st.session_state.run_triggered = False # Reset trigger on error
        except subprocess.CalledProcessError as e:
            st.error(f"Error executing backend script: {e}")
            st.session_state.backend_output += f"Error executing backend script: {e}\nStderr: {e.stderr}\nStdout: {e.stdout}\n"
            backend_output_area.text_area("Backend Output", st.session_state.backend_output, height=300)
            st.session_state.run_triggered = False # Reset trigger on error
        except json.JSONDecodeError:
            st.error("Error decoding JSON from crew_result.json. Ensure the backend script outputs valid JSON.")
            st.session_state.backend_output += "Error decoding JSON from crew_result.json.\n"
            backend_output_area.text_area("Backend Output", st.session_state.backend_output, height=300)
            st.session_state.run_triggered = False # Reset trigger on error
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            st.session_state.backend_output += f"An unexpected error occurred: {str(e)}\n"
            backend_output_area.text_area("Backend Output", st.session_state.backend_output, height=300)
            st.session_state.run_triggered = False # Reset trigger on error


# Display results if available
#st.write("Debug: st.session_state.results state:", st.session_state.results)
if st.session_state.results and "recommendations" in st.session_state.results:
    recommendations = st.session_state.results.get("recommendations", []) # Use .get for safety

    if recommendations:
        st.header("Investment Recommendations")
        for rec in recommendations:
            ticker = rec.get("ticker", "N/A")
            recommendation = rec.get("recommendation", "N/A")
            reasoning = rec.get("reasoning", "No reasoning provided.")
            forecast = rec.get("forecast", {})

            st.subheader(f"{ticker}: {recommendation}")
            st.markdown("**Reasoning:**")
            st.write(reasoning)

            if forecast:
                st.markdown("**Forecasts:**")
                if isinstance(forecast, dict): # Add check if forecast is a dictionary
                    for model, data in forecast.items():
                        st.write(f"- **{model}:**")
                        if isinstance(data, dict): # Add check if data is a dictionary
                            for metric, value in data.items():
                                if isinstance(value, float):
                                    st.write(f"  - {metric}: {value:.2f}")
                                else:
                                    st.write(f"  - {metric}: {value}")
                        else:
                            st.write(f"  - Details: {data}") # Display the string if not a dictionary
                else: # Handle case where forecast is not a dictionary
                    st.write(f"  - Forecast data format unexpected: {forecast}")
            else:
                st.info("No forecast data available for this ticker.")
            st.markdown("---") # Separator for clarity
    else:
        st.info("No investment recommendations available.")

# Download Report Section
st.header("Download Report")

# Button to trigger PDF generation and download
if st.button("Download PDF Report"):
    #st.write("Debug: st.session_state.results state:", st.session_state.results)
    # Check if results are available before generating PDF
    # Relaxing the condition to only check for recommendations for now
    if not st.session_state.results or not st.session_state.results.get("recommendations"):
        st.warning("Please run the analysis pipeline first to generate results before downloading the report.")
        st.stop() # Stop execution if no results

    st.info("Generating PDF report...")
    st.write("Debug: Content of st.session_state.results before sending to backend:", st.session_state.results) # Added debug line
    try:
        # Assuming backend is running on http://localhost:8000
        backend_url = "http://localhost:8000/reports/generate"
        # Pass the results from the session state to the backend
       # Construct the data payload for the backend
        report_data = {
            "stock_data": st.session_state.results.get("research", {}), # Keep sending empty dict if not available
            "analysis_results": st.session_state.results.get("analysis", {}), # Keep sending empty dict if not available
            "llm_recommendations": {rec.get("ticker"): rec for rec in st.session_state.results.get("recommendations", []) if rec.get("ticker")}
        }
        response = requests.post(backend_url, json=report_data)

        if response.status_code == 200:
            # Get filename from headers if available, otherwise use a default
            content_disposition = response.headers.get("Content-Disposition")
            if content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"stock_analysis_report_{timestamp}.pdf"

            st.download_button(
                label="Click here to download",
                data=response.content,
                file_name=filename,
                mime="application/pdf"
            )
            st.success("PDF report generated and ready for download.")
        else:
            st.error(f"Error generating PDF report: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Error connecting to the backend. Please ensure the backend is running.")
    except Exception as e:
        st.error(f"An unexpected error occurred during PDF generation: {str(e)}")


# Download Raw Data
st.header("Download Raw Data")
results_file_path = "../backend/outputs/crew_result.json" # Updated path
if os.path.exists(results_file_path):
    try:
        with open(results_file_path, "r") as f:
            st.download_button(
                label="Download JSON Results",
                data=f,
                file_name="crew_result.json",
                mime="application/json"
            )
    except FileNotFoundError:
        st.warning("Results file not found. Please run the analysis again.")
    else:
         st.info("Results file not found. Run the analysis pipeline to generate results.")


if not st.session_state.run_triggered and not st.session_state.get("final", {}):
    st.info("Enter stock symbols and click 'Start Analysis Pipeline' to begin.")
