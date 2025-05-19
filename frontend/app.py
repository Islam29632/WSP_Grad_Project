import os, json, time, subprocess, requests
from datetime import datetime
from typing import Dict, List

import streamlit as st
import pandas as pd
import plotly.express as px
import math # Added for math.isnan

from auth import init_auth_state, login, signup
import pathlib
import sys

# Setup path resolution
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding='utf-8')


from backend.agent_main_call import run_crew

# Helper function to replace NaN with None for JSON compatibility
def replace_nan_with_none(obj):
    if isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan_with_none(elem) for elem in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    return obj

# ╭──────────────────────────────────────────────╮
# │ 1. Page & session-state                      │
# ╰──────────────────────────────────────────────╯
st.set_page_config(page_title="Stock Analysis App", layout="wide")

init_auth_state()
ss = st.session_state
ss.setdefault("results",        {"research": {}, "analysis": {}, "recommendations": [], "raw_price_data": [], "ticker_analysis": {}})
ss.setdefault("run_triggered",  False)
ss.setdefault("backend_log",    "")
ss.setdefault("pdf_content", None)
ss.setdefault("pdf_filename", "")

# login / signup wall
if not ss.get("authenticated", False):
    (signup() if ss.get("show_signup", False) else login())
    st.stop()


# ╭──────────────────────────────────────────────╮
# │ 2. Input form                                │
# ╰──────────────────────────────────────────────╯
st.title("Stock Analysis Pipeline")

symbols_str = st.text_input("Stock Symbols (comma-separated)", "AAPL, AMD, GOOGL")
user_pov    = "I'm a conservative investor looking for stable growth with low risk."

if st.button("Start Analysis Pipeline"):
    syms = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
    if syms:
        ss.run_triggered = True
        # Reset results and PDF content for a new run
        ss.results       = {"research": {}, "analysis": {}, "recommendations": [], "raw_price_data": [], "ticker_analysis": {}}
        ss.backend_log   = ""
        ss.pdf_content = None
        ss.pdf_filename = ""
        st.rerun()


# ╭──────────────────────────────────────────────╮
# │ 3. Run back-end scripts when triggered       │
# ╰──────────────────────────────────────────────╯
# st.sidebar.write(f"Debug: ss.run_triggered = {ss.run_triggered}") # Optional: for debugging

if ss.run_triggered:
    syms = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
    if not syms:
        st.error("No valid symbols supplied.")
        ss.run_triggered = False
        st.stop()

    result_json_path = "../backend/outputs/crew_result.json"
    forecast_json_path = "../backend/outputs/forecast_results.json"
    ticker_analysis_path = "../backend/outputs/ticker_analysis.json"
    raw_prices_csv_path = "../backend/data/raw/World-Stock-Prices-Dataset.csv"

    # Initialize data containers for this run
    crew_data = None
    forecast_data = {} # Default to empty dict

    with st.status("Running analysis …", expanded=True) as status:
        # Step-1: Kaggle dataset check / download
        message_1 = st.empty()
        message_1.write("⇣ Checking Kaggle dataset …")
        t0 = time.time()
        try:
            subprocess.run(["python", "../backend/database/pipeline_dataset.py"], check=True, capture_output=True, text=True)
            message_1.empty()
            status.write(f"✔️ Dataset Updated - {datetime.now().strftime('%B %d, %Y')} ({time.time()-t0:.1f}s)")
        except subprocess.CalledProcessError as e:
            status.update(label="Dataset update script failed.", state="error", expanded=True)
            st.error(f"Error during dataset update: {e}\nOutput:\n{e.stdout}\n{e.stderr}")
            ss.run_triggered = False
            st.stop()
        except Exception as e:
            status.update(label="Dataset update failed.", state="error", expanded=True)
            st.error(f"Error during dataset update: {e}")
            ss.run_triggered = False
            st.stop()


        # Step-2: Crew pipeline (run directly from Python)
        message_2 = st.empty()
        message_2.write("🤖 Launching Crew agents …")
        t0 = time.time()
        try:
            run_crew(syms, user_pov) # This function should create/update the JSON files
            message_2.empty()
            status.write(f"✔️ Crew finished ({time.time()-t0:.1f}s)")
        except Exception as e:
            status.update(label="Crew pipeline failed.", state="error", expanded=True)
            st.error(f"Error during Crew run: {e}")
            ss.run_triggered = False
            st.stop()

        # Step-3: Load results from backend outputs
        message_3 = st.empty()
        message_3.write("🔄 Loading and processing results...")
        t1 = time.time()
        message_3.empty()
        status.write(f"✔️ Loaded and processed results ({time.time()-t1:.1f}s)")
        try:
            with open(result_json_path) as f:
                crew_data = json.load(f)
        except FileNotFoundError:
            status.update(label=f"{os.path.basename(result_json_path)} not found – pipeline may have failed or not created the file.", state="error", expanded=True)
            ss.run_triggered = False; st.stop()
        except json.JSONDecodeError:
            status.update(label=f"Error decoding {os.path.basename(result_json_path)} – pipeline failed.", state="error", expanded=True)
            ss.run_triggered = False; st.stop()
        
        try:
            with open(forecast_json_path) as f1:
                forecast_data = json.load(f1)
        except FileNotFoundError:
            status.write(f"⚠️ {os.path.basename(forecast_json_path)} not found. Forecast data may be missing from recommendations.")
            forecast_data = {} # Default to empty if not found
        except json.JSONDecodeError:
            status.write(f"⚠️ Error decoding {os.path.basename(forecast_json_path)}. Forecast data may be missing or incomplete.")
            forecast_data = {} # Default to empty on error

        # Load raw price data for the report payload
        try:
            df_raw = pd.read_csv(raw_prices_csv_path)
            if "Date" not in df_raw.columns:
                status.write(f"⚠️ 'Date' column not found in {os.path.basename(raw_prices_csv_path)}. Raw price data for report will be empty or incomplete.")
                ss.results["raw_price_data"] = [] 
            else:
                df_raw["Date"] = pd.to_datetime(df_raw["Date"], errors='coerce')
                df_raw = df_raw.dropna(subset=['Date']) 
                if not df_raw.empty:
                    if pd.api.types.is_datetime64_any_dtype(df_raw['Date']):
                        df_raw["Date"] = df_raw["Date"].dt.strftime('%Y-%m-%d')
                    else:
                        df_raw["Date"] = df_raw["Date"].astype(str)
                ss.results["raw_price_data"] = df_raw.to_dict(orient="records")
        except FileNotFoundError:
            status.write(f"⚠️ Raw data CSV ({os.path.basename(raw_prices_csv_path)}) not found. Raw price data will not be included in the report.")
            ss.results["raw_price_data"] = [] 
        except Exception as e:
            status.write(f"🚨 Critical error loading raw price data for report: {e}") 
            ss.results["raw_price_data"] = []
        
        # Load ticker analysis data for the report payload and Section 5 display
        try:
            with open(ticker_analysis_path) as f2:
                ticker_analysis_data = json.load(f2)
                ss.results["ticker_analysis"] = ticker_analysis_data
        except FileNotFoundError:
            status.write(f"⚠️ {os.path.basename(ticker_analysis_path)} not found. Ticker analysis data will be missing.")
            ss.results["ticker_analysis"] = {} # Default to empty dict
        except json.JSONDecodeError:
            status.write(f"⚠️ Error decoding {os.path.basename(ticker_analysis_path)}. Ticker analysis data may be incomplete.")
            ss.results["ticker_analysis"] = {}


        # Normalize crew_data and forecast_data into ss.results["recommendations"]
        processed_recommendations = []
        if isinstance(crew_data, dict):
            # Option 1: crew_data has a top-level "recommendations" list
            if "recommendations" in crew_data and isinstance(crew_data["recommendations"], list):
                for rec_item in crew_data["recommendations"]:
                    if isinstance(rec_item, dict) and "ticker" in rec_item:
                        ticker = rec_item.get("ticker")
                        # Ensure forecast is present, using forecast_data as primary source if rec_item lacks it
                        if not rec_item.get("forecast") and ticker and forecast_data.get(ticker):
                            rec_item["forecast"] = forecast_data.get(ticker, {})
                        processed_recommendations.append(rec_item)
            # Option 2: crew_data has a "final" object to be transformed
            elif "final" in crew_data and isinstance(crew_data["final"], dict):
                for ticker_key, final_item_val in crew_data["final"].items():
                    if not isinstance(final_item_val, dict): continue 
                    processed_recommendations.append({
                        "ticker": ticker_key,
                        "recommendation": final_item_val.get("rule_based", ["Hold"])[0],
                        "reasoning": final_item_val.get("llm_advice", ""),
                        "forecast": forecast_data.get(ticker_key, final_item_val.get("forecast", {}))
                    })
            else:
                status.write("⚠️ crew_result.json (dict) is missing 'recommendations' list or 'final' object. Recommendations may be incomplete.")
            # Copy other keys from crew_data to ss.results if needed (be cautious about overwriting)
            # For now, only explicitly populate known structures. Add ss.results.update(crew_data) if other keys are expected.

        elif isinstance(crew_data, list):
            # Assume crew_data is already a list of recommendations
            for rec_item in crew_data:
                if isinstance(rec_item, dict) and "ticker" in rec_item:
                    ticker = rec_item.get("ticker")
                    if not rec_item.get("forecast") and ticker and forecast_data.get(ticker):
                         rec_item["forecast"] = forecast_data.get(ticker, {})
                    processed_recommendations.append(rec_item)
        else:
            status.write("⚠️ crew_result.json did not contain valid data (expected dict or list). Recommendations will be empty.")
        
        ss.results["recommendations"] = processed_recommendations

        status.update(label="Pipeline completed", state="complete", expanded=True) # Collapse on completion
        ss.run_triggered = False # Crucial: set to False only after all steps inside are done
        st.success("Analysis complete – scroll for results.")
        # Do not call st.rerun() here, let Streamlit flow naturally

# ╭──────────────────────────────────────────────╮
# │ 4. Display raw price data from CSV           │
# ╰──────────────────────────────────────────────╯
st.subheader("1. Raw price data from CSV")

csv_display_path = "../backend/data/raw/World-Stock-Prices-Dataset.csv" # Use a different var name if needed
try:
    df_raw_display = pd.read_csv(csv_display_path)
    df_raw_display["Date"] = pd.to_datetime(df_raw_display["Date"], errors='coerce')
    df_raw_display.dropna(subset=['Date'], inplace=True)

    user_symbols_for_display = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]

    if user_symbols_for_display:
        df_filtered_display = df_raw_display[df_raw_display["Ticker"].isin(user_symbols_for_display)].copy()
        if not df_filtered_display.empty:
            fig = px.line(df_filtered_display, x="Date", y="Close", color="Ticker",
                          title="Raw Price Data for Selected Symbols")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No raw data found for the entered symbols in the CSV.")
    else:
        st.info("Please enter stock symbols to display raw data.")
except FileNotFoundError:
    st.error(f"Raw data CSV for display not found at {csv_display_path}")
except Exception as e:
    st.error(f"Error loading or plotting raw data for display: {e}")

# ╭──────────────────────────────────────────────╮
# │ 5. Plot Price and Growth Analysis            │
# ╰──────────────────────────────────────────────╯
if ss.results.get("ticker_analysis") and isinstance(ss.results["ticker_analysis"], dict) and ss.results["ticker_analysis"]:
    st.subheader("2. Highest/Lowest Price and Growth Percentage per Ticker")
    analysis_data_display = ss.results["ticker_analysis"]
    plot_data_display = []
    
    user_symbols_for_plot = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]    
    if user_symbols_for_plot:
        for ticker_plot in user_symbols_for_plot:
            if ticker_plot in analysis_data_display:
                data_item = analysis_data_display[ticker_plot]
                if data_item.get("highest_price") is not None:
                    plot_data_display.append({"Ticker": ticker_plot, "Metric": "Highest Price", "Value": data_item["highest_price"]})
                if data_item.get("lowest_price") is not None:
                    plot_data_display.append({"Ticker": ticker_plot, "Metric": "Lowest Price", "Value": data_item["lowest_price"]})
                if data_item.get("growth_2020_percent") is not None:
                    plot_data_display.append({"Ticker": ticker_plot, "Metric": "Growth Percentage", "Value": data_item["growth_2020_percent"]})

        if plot_data_display:
            df_analysis_plot = pd.DataFrame(plot_data_display)
            fig_analysis_plot = px.bar(df_analysis_plot, x="Ticker", y="Value", color="Metric",
                                  title="Ticker Price and Growth Analysis", barmode="group")
            st.plotly_chart(fig_analysis_plot, use_container_width=True)
        else:
            st.info("No ticker analysis data available for the entered symbols after pipeline run.")
elif not ss.run_triggered and not any(ss.results.get(k) for k in ["recommendations", "ticker_analysis"]): # Only show if pipeline hasn't run or produced nothing
    st.info("Run the analysis pipeline to see ticker price and growth analysis.")


# ╭──────────────────────────────────────────────╮
# │ 6. Recommendations                           │
# ╰──────────────────────────────────────────────╯
st.subheader("3. Investment recommendations")
if ss.results["recommendations"]:
    for rec in ss.results["recommendations"]:
        # Ensure rec is a dictionary and has expected keys before trying to access them
        if isinstance(rec, dict) and "ticker" in rec and "recommendation" in rec:
            st.markdown(f"### {rec['ticker']} – {rec['recommendation']}")
            st.write(rec.get("reasoning", "No reasoning provided."))
            if rec.get("forecast"): # Check if forecast key exists and is not empty/None
                try:
                    st.json(rec["forecast"], expanded=True) # Start collapsed
                except Exception as e:
                    st.warning(f"Could not display forecast for {rec['ticker']}: {e}")
            st.markdown("---")
        else:
            st.warning("Received an improperly formatted recommendation.")
else:
    st.info("No investment recommendations available. Please run the analysis pipeline or check pipeline results if it has been run.")


# ╭──────────────────────────────────────────────╮
# │ 6.1 Forecast vs. Actual Prices               │
# ╰──────────────────────────────────────────────╯
st.subheader("3.1 Forecast vs. Actual Prices")
forecast_plot_json_path = "../backend/outputs/forecast_results.json"
plot_forecast_data = []
user_symbols_for_forecast_plot = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]

if os.path.exists(forecast_plot_json_path) and user_symbols_for_forecast_plot:
    try:
        with open(forecast_plot_json_path) as f_plot:
            loaded_forecast_data = json.load(f_plot)

        for ticker_symbol in user_symbols_for_forecast_plot:
            if ticker_symbol in loaded_forecast_data:
                data = loaded_forecast_data[ticker_symbol]
                actual_price = data.get("actual_price")
                lstm_forecast = data.get("LSTM", {}).get("forecast")
                mlp_forecast = data.get("MLP", {}).get("forecast")

                if actual_price is not None:
                    plot_forecast_data.append({"Ticker": ticker_symbol, "Value Type": "Actual Price", "Price": actual_price})
                if lstm_forecast is not None:
                    plot_forecast_data.append({"Ticker": ticker_symbol, "Value Type": "LSTM Forecast", "Price": lstm_forecast})
                if mlp_forecast is not None:
                    plot_forecast_data.append({"Ticker": ticker_symbol, "Value Type": "MLP Forecast", "Price": mlp_forecast})
            else:
                st.caption(f"No forecast data found for {ticker_symbol} in {os.path.basename(forecast_plot_json_path)}.")
        
        if plot_forecast_data:
            df_forecast_plot = pd.DataFrame(plot_forecast_data)
            fig_forecast_plot = px.bar(df_forecast_plot, x="Ticker", y="Price", color="Value Type",
                                       title="Forecast vs. Actual Prices by Ticker", barmode="group")
            st.plotly_chart(fig_forecast_plot, use_container_width=True)
        else:
            st.info("No forecast data processed for the selected symbols to display the plot. Ensure the forecast file contains data for your selected symbols.")

    except json.JSONDecodeError:
        st.error(f"Error decoding {os.path.basename(forecast_plot_json_path)}. The file might be corrupted.")
    except Exception as e:
        st.error(f"An error occurred while preparing the forecast vs. actual prices plot: {e}")
elif not user_symbols_for_forecast_plot:
    st.info("Please enter stock symbols to see the forecast vs. actual prices plot.")
else:
    st.info(f"{os.path.basename(forecast_plot_json_path)} not found. Run the pipeline to generate forecast data.")


# ╭──────────────────────────────────────────────╮
# │ 7. PDF report download                       │
# ╰──────────────────────────────────────────────╯
st.header("4. Download PDF report")

if st.button("Generate PDF Report"):
    if not ss.results.get("recommendations") and not ss.results.get("raw_price_data") and not ss.results.get("ticker_analysis"):
        st.warning("No data available to generate a report. Please run the analysis pipeline first.")
        st.stop()
    
    # Prepare forecast data for PDF payload
    forecast_pdf_data = {}
    forecast_data_path_for_pdf = "../backend/outputs/forecast_results.json" # Already defined above, ensure consistency
    user_symbols_list_for_pdf = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]

    if os.path.exists(forecast_data_path_for_pdf):
        try:
            with open(forecast_data_path_for_pdf) as f_pdf:
                loaded_forecast_pdf_data = json.load(f_pdf)
            for sym in user_symbols_list_for_pdf:
                if sym in loaded_forecast_pdf_data:
                    forecast_pdf_data[sym] = loaded_forecast_pdf_data[sym]
        except Exception as e:
            st.warning(f"Could not load forecast data for PDF report: {e}")
            # forecast_pdf_data will remain empty or partially filled

    try:
        backend_url = "http://localhost:8000/reports/generate" # Ensure backend is running at this address
        user_symbols_list = [s.strip().upper() for s in symbols_str.split(",") if s.strip()] # Redundant if using user_symbols_list_for_pdf
        payload = {
            "raw_price_data_payload": ss.results.get("raw_price_data", []),
            "analysis_results_payload": ss.results.get("ticker_analysis", {}),
            "llm_recommendations_payload": {r["ticker"]: r for r in ss.results.get("recommendations", []) if isinstance(r, dict) and "ticker" in r},
            "research_data_payload": ss.results.get("research", {}), 
            "user_symbols_payload": user_symbols_list,
            "forecast_vs_actual_payload": forecast_pdf_data, # Add forecast data to payload
        }
        
        # Clean payload from NaN values
        cleaned_payload = replace_nan_with_none(payload)
        
        with st.spinner("Generating PDF... Please wait."):
            r = requests.post(backend_url, json=cleaned_payload, timeout=120) # Use cleaned_payload
            r.raise_for_status() # Will raise HTTPError for bad responses (4xx or 5xx)
        
        ss.pdf_content = r.content
        ss.pdf_filename = (
            r.headers.get("Content-Disposition", "")
              .split("filename=")[-1].strip('"')
            or f"stock_report_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        )
        st.success(f"PDF report '{ss.pdf_filename}' generated successfully. Click below to download.")
        # Rerun to make download button appear in the next script pass
        st.rerun()

    except requests.exceptions.ConnectionError:
        st.error("Failed to connect to the backend PDF generation service. Is it running at http://localhost:8000?")
        ss.pdf_content = None
    except requests.exceptions.Timeout:
        st.error("PDF generation request timed out. The backend might be too slow or unresponsive.")
        ss.pdf_content = None
    except requests.exceptions.HTTPError as e:
        st.error(f"PDF generation failed with HTTP status {e.response.status_code}: {e.response.text}")
        ss.pdf_content = None
    except Exception as e:
        st.error(f"An unexpected error occurred during PDF generation: {e}")
        ss.pdf_content = None

if ss.pdf_content and ss.pdf_filename:
    st.download_button("Download PDF Report", ss.pdf_content,
                       file_name=ss.pdf_filename, mime="application/pdf")


# ╭──────────────────────────────────────────────╮
# │ 8. Raw JSON download                         │
# ╰──────────────────────────────────────────────╯
st.header("5. Download raw JSON output from Crew")
crew_output_path = "../backend/outputs/crew_result.json"
if os.path.exists(crew_output_path):
    try:
        with open(crew_output_path, "rb") as f: # Read as binary for download button
            st.download_button(f"Download {os.path.basename(crew_output_path)}", f,
                               file_name=os.path.basename(crew_output_path),
                               mime="application/json")
    except Exception as e:
        st.error(f"Could not prepare {os.path.basename(crew_output_path)} for download: {e}")
else:
    st.info(f"{os.path.basename(crew_output_path)} not found. Run the pipeline to generate it.")


# footer hint
st.markdown("---")
st.info("Enter stock symbols then press **Start Analysis Pipeline** to begin.")
