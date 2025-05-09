import streamlit as st
import pandas as pd
import plotly.express as px
import json
from auth import init_auth_state, login, signup
# from api.crew import run_crew  # Import run_crew function

# Page configuration
st.set_page_config(page_title="Stock Analysis App", layout="wide")

# Initialize session states
init_auth_state()
if "results" not in st.session_state:
    st.session_state.results = {"research": {}, "analysis": {}, "final": {}}
if "run_triggered" not in st.session_state:
    st.session_state.run_triggered = False

# Handle authentication
if not st.session_state["authenticated"]:
    if st.session_state.get("show_signup", False):
        signup()
    else:
        login()
    st.stop()

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Welcome", "Analysis"])

# Welcome Page
if page == "Welcome":
    st.title("Welcome to the Stock Analysis App")
    st.markdown("""
        This app fetches and analyzes stock data, providing trends, anomalies, and investment proposals.
        Navigate to the **Analysis** page to:
        - Enter stock symbols (e.g., AAPL).
        - Run the analysis.
        - View results and price forecasts.
    """)
    st.info("Use the sidebar to switch to the Analysis page.")

# Analysis Page
elif page == "Analysis":
    st.title("Stock Analysis")
    st.markdown("Enter stock symbols to analyze data and view forecasts.")

    # Inputs
    default_symbols = "AAPL"
    symbols_input = st.text_input(
        "Stock Symbols (comma-separated)", default_symbols)
    user_pov = "I’m a conservative investor looking for stable growth with low risk."
    run_button = st.button("Run Analysis")

    # Parse symbols
    def parse_symbols(input_string):
        symbols = [s.strip().upper()
                   for s in input_string.split(",") if s.strip()]
        if not symbols:
            st.error("Please enter at least one valid stock symbol.")
            return None
        return symbols

    # Run analysis
    if run_button:
        symbols = parse_symbols(symbols_input)
        if symbols:
            with st.spinner("Running analysis..."):
                try:
                    research_output, analysis_output, final_output = run_crew(
                        symbols, user_pov)
                    st.session_state.results = {
                        "research": research_output,
                        "analysis": analysis_output,
                        "final": final_output
                    }
                    with open("crew_result.json", "w") as f:
                        json.dump(final_output, f, indent=2)
                    st.session_state.run_triggered = True
                    st.success("Analysis completed!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Display results
    if st.session_state.run_triggered and st.session_state.results["final"]:
        results = st.session_state.results
        research_output = results["research"]
        analysis_output = results["analysis"]
        final_output = results["final"]

        # Raw Data
        st.header("Raw Stock Data")
        for symbol in research_output:
            if "error" not in research_output[symbol]:
                st.subheader(symbol)
                df = pd.DataFrame(
                    list(research_output[symbol].items()), columns=["Date", "Price"])
                df["Date"] = pd.to_datetime(df["Date"])
                st.dataframe(df.sort_values("Date")[
                             ["Date", "Price"]], use_container_width=True)
            else:
                st.warning(f"{symbol}: {research_output[symbol]['error']}")

        # Price Plot
        st.header("Price History and Forecast")
        for symbol in research_output:
            if "error" not in research_output[symbol] and symbol in analysis_output and "error" not in analysis_output[symbol]:
                df = pd.DataFrame(
                    list(research_output[symbol].items()), columns=["Date", "Price"])
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.sort_values("Date")

                # Add forecast
                forecast = analysis_output[symbol]["forecast_next_month"]
                last_date = df["Date"].max()
                forecast_date = last_date + pd.offsets.MonthEnd(1)
                forecast_df = pd.DataFrame({"Date": [forecast_date], "Price": [
                                           forecast], "Type": ["Forecast"]})
                df["Type"] = "Historical"
                plot_df = pd.concat([df, forecast_df], ignore_index=True)

                # Plot
                fig = px.line(plot_df, x="Date", y="Price", color="Type",
                              title=f"{symbol} Price History and Forecast")
                fig.add_scatter(x=[forecast_date], y=[
                                forecast], mode="markers", name="Forecast Point", marker=dict(size=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"{symbol}: Cannot plot due to data error.")

        # Analysis Results
        st.header("Analysis Results")
        for symbol in analysis_output:
            if "error" not in analysis_output[symbol]:
                st.subheader(symbol)

                # Basic Stats
                st.markdown("**Basic Statistics**")
                stats_df = pd.DataFrame({
                    "Metric": ["Average Price", "Max Price", "Min Price"],
                    "Value": [
                        analysis_output[symbol]["basic_stats"]["average_price"],
                        analysis_output[symbol]["basic_stats"]["max_price"],
                        analysis_output[symbol]["basic_stats"]["min_price"]
                    ]
                })
                st.dataframe(stats_df, use_container_width=True)

                # Month-over-Month Changes
                st.markdown("**Recent Month-over-Month Changes (%)**")
                changes_df = pd.DataFrame({
                    "Change (%)": analysis_output[symbol]["basic_stats"]["month_over_month_changes"][-5:]
                })
                st.dataframe(changes_df, use_container_width=True)

                # Trend
                st.markdown("**Trend**")
                st.write(
                    f"Direction: {analysis_output[symbol]['trend']['direction']}, Slope: {analysis_output[symbol]['trend']['slope']:.4f}")

                # Anomalies
                st.markdown("**Anomalies**")
                if analysis_output[symbol]["anomalies"]:
                    anomalies_df = pd.DataFrame(
                        analysis_output[symbol]["anomalies"])
                    st.dataframe(anomalies_df, use_container_width=True)
                else:
                    st.write("No anomalies detected.")

                # Forecast
                st.markdown("**Next Month Forecast**")
                st.write(
                    f"Predicted Price: ${analysis_output[symbol]['forecast_next_month']:.2f}")
            else:
                st.warning(f"{symbol}: {analysis_output[symbol]['error']}")

        # Investment Proposals
        st.header("Investment Proposals")
        for symbol in final_output:
            if "error" not in final_output[symbol]:
                st.subheader(symbol)
                st.markdown("**Rule-Based Recommendations**")
                for rule in final_output[symbol]["rule_based"]:
                    st.write(f"- {rule}")
                st.markdown("**LLM Advice**")
                st.markdown(final_output[symbol]["llm_advice"])
            else:
                st.warning(f"{symbol}: {final_output[symbol]['error']}")

        # Download Results
        st.header("Download Results")
        try:
            with open("crew_result.json", "r") as f:
                st.download_button(
                    label="Download JSON Results",
                    data=f,
                    file_name="crew_result.json",
                    mime="application/json"
                )
        except FileNotFoundError:
            st.warning("Results file not found. Please run the analysis again.")

    if not st.session_state.run_triggered:
        st.info("Enter stock symbols and click 'Run Analysis' to view results.")
