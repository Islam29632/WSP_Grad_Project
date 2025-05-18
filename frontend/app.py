import os, json, time, subprocess, requests
from datetime import datetime
from typing import Dict, List

import streamlit as st
import pandas as pd
import plotly.express as px

from auth import init_auth_state, login, signup
import pathlib
import sys

# Setup path resolution
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BASE_DIR))


from backend.agent_main_call import run_crew


# ╭──────────────────────────────────────────────╮
# │ 1. Page & session-state                      │
# ╰──────────────────────────────────────────────╯
st.set_page_config(page_title="Stock Analysis App", layout="wide")

init_auth_state()
ss = st.session_state
ss.setdefault("results",        {"research": {}, "analysis": {}, "recommendations": []})
ss.setdefault("run_triggered",  False)
ss.setdefault("backend_log",    "")

# login / signup wall
if not ss.get("authenticated", False):
    (signup() if ss.get("show_signup", False) else login())
    st.stop()


# ╭──────────────────────────────────────────────╮
# │ 2. Input form                                │
# ╰──────────────────────────────────────────────╯
st.title("Stock Analysis Pipeline")

symbols_str = st.text_input("Stock Symbols (comma-separated)", "AAPL")
user_pov    = "I'm a conservative investor looking for stable growth with low risk."

if st.button("Start Analysis Pipeline"):
    syms = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
    if syms:
        ss.run_triggered = True
        ss.results       = {"research": {}, "analysis": {}, "recommendations": []}
        ss.backend_log   = ""
        st.rerun()


# ╭──────────────────────────────────────────────╮
# │ 3. Run back-end scripts when triggered       │
# ╰──────────────────────────────────────────────╯
if ss.run_triggered:
    syms = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
    if not syms:
        st.error("No valid symbols supplied.")
        ss.run_triggered = False
        st.stop()

    result_json_path = "backend/outputs/crew_result.json"

    with st.status("Running analysis …", expanded=True) as status:
        # Step-1: Kaggle dataset check / download
        status.write("⇣ Checking Kaggle dataset …")
        t0 = time.time()
        subprocess.run(["python", "backend/database/pipeline_dataset.py"], check=True)
        status.write(f"✓ Dataset ready ({time.time()-t0:.1f}s)")

        # Step-2: Crew pipeline (run directly from Python)
        status.write("🤖 Launching Crew agents …")
        t0 = time.time()
        try:
            run_crew(syms, user_pov)
            status.write(f"✓ Crew finished ({time.time()-t0:.1f}s)")
        except Exception as e:
            status.update(label="Crew pipeline failed.", state="error", expanded=True)
            st.error(f"Error during Crew run: {e}")
            ss.run_triggered = False
            st.stop()

        # Step-3: load results
        if not os.path.exists(result_json_path):
            status.update(label="crew_result.json not found – pipeline failed.",
                          state="error", expanded=True)
            ss.run_triggered = False
            st.stop()

        with open(result_json_path) as f:
            data = json.load(f)

        # normalise into session-state
        if isinstance(data, dict):
            ss.results.update(data)
            if "recommendations" not in data:
                ss.results["recommendations"] = [
                    {"ticker": k,
                     "recommendation": v.get("rule_based", ["Hold"])[0]
                     if isinstance(v, dict) else "N/A",
                     "reasoning": v.get("llm_advice", "") if isinstance(v, dict) else "",
                     "forecast": v.get("forecast", {}) if isinstance(v, dict) else {}}
                    for k, v in data.get("final", {}).items()
                ]
        elif isinstance(data, list):
            ss.results["recommendations"] = data

        status.update(label="Pipeline completed ✓", state="complete", expanded=True)

    ss.run_triggered = False
    st.success("Analysis complete – scroll for results.")


# ╭──────────────────────────────────────────────╮
# │ 4. Display raw research data                 │
# ╰──────────────────────────────────────────────╯
if ss.results["research"]:
    st.subheader("Raw price data (cut-off 2024-12-31)")
    for sym, series in ss.results["research"].items():
        df = pd.DataFrame(series.items(), columns=["Date", "Price"])
        df["Date"] = pd.to_datetime(df["Date"])
        st.write(sym)
        st.dataframe(df.sort_values("Date"), use_container_width=True)


# ╭──────────────────────────────────────────────╮
# │ 5. Plot history + forecast                   │
# ╰──────────────────────────────────────────────╯
if ss.results["analysis"]:
    st.subheader("Price history and forecast (first trading day Jan-2025)")
    for sym, info in ss.results["analysis"].items():
        hist_series = ss.results["research"].get(sym)
        if not hist_series or not info:
            continue

        df_hist = (pd.DataFrame(hist_series.items(), columns=["Date", "Price"])
                     .assign(Date=lambda d: pd.to_datetime(d["Date"]))
                     .sort_values("Date"))

        f_val  = info.get("forecast_value")
        f_date = info.get("forecast_date")
        if f_val is None or f_date is None:
            continue

        df_fore = pd.DataFrame({"Date": [pd.to_datetime(f_date)],
                                "Price": [f_val],
                                "Type": ["Forecast"]})
        df_hist["Type"] = "Historical"
        plot_df = pd.concat([df_hist, df_fore])

        fig = px.line(plot_df, x="Date", y="Price", color="Type",
                      title=f"{sym} history vs forecast")
        st.plotly_chart(fig, use_container_width=True)


# ╭──────────────────────────────────────────────╮
# │ 6. Recommendations                           │
# ╰──────────────────────────────────────────────╯
if ss.results["recommendations"]:
    st.subheader("Investment recommendations")
    for rec in ss.results["recommendations"]:
        st.markdown(f"### {rec['ticker']} – {rec['recommendation']}")
        st.write(rec.get("reasoning", ""))
        if rec.get("forecast"):
            st.json(rec["forecast"], expanded=False)
        st.markdown("---")


# ╭──────────────────────────────────────────────╮
# │ 7. PDF report download                       │
# ╰──────────────────────────────────────────────╯
st.header("Download PDF report")
if st.button("Generate & download"):
    if not ss.results["recommendations"]:
        st.warning("Run the pipeline first.")
        st.stop()

    try:
        backend_url = "http://localhost:8000/reports/generate"
        payload = {
            "stock_data":        ss.results.get("research", {}),
            "analysis_results":  ss.results.get("analysis", {}),
            "llm_recommendations":
                {r["ticker"]: r for r in ss.results["recommendations"]}
        }
        r = requests.post(backend_url, json=payload)
        r.raise_for_status()

        filename = (
            r.headers.get("Content-Disposition", "")
              .split("filename=")[-1].strip('"')
            or f"stock_report_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        )
        st.download_button("Download PDF", r.content,
                           file_name=filename, mime="application/pdf")
    except Exception as e:
        st.error(f"PDF generation failed → {e}")


# ╭──────────────────────────────────────────────╮
# │ 8. Raw JSON download                         │
# ╰──────────────────────────────────────────────╯
st.header("Download raw JSON")
if os.path.exists("backend/outputs/crew_result.json"):
    with open("backend/outputs/crew_result.json", "rb") as f:
        st.download_button("crew_result.json", f, mime="application/json")


# footer hint
st.info("Enter stock symbols then press **Start Analysis Pipeline**.")
