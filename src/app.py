import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from quant_insider_core import (
    load_insider_buys,
    tag_large_buys,
    compute_forward_returns,
    summarize_returns,
)

st.set_page_config(
    page_title="Insider Buy Reaction – Quant MVP",
    layout="wide",
)


# ----------------------------------------------------
# RUN PIPELINE
# ----------------------------------------------------
@st.cache_data(show_spinner=True)
def run_pipeline(min_value_usd, start_date, end_date, quantile, horizon):
    buys = load_insider_buys(
        min_value_usd=min_value_usd,
        start_date=start_date,
        end_date=end_date,
    )
    if buys.empty:
        return buys, buys, pd.DataFrame(), {}

    buys = tag_large_buys(buys, quantile)
    results = compute_forward_returns(buys, horizon)
    summary, stats = summarize_returns(results, horizon)
    return buys, results, summary, stats


# ----------------------------------------------------
# DASHBOARD UI
# ----------------------------------------------------
def main():
    st.title("📈 Insider Purchase Reaction – Quant MVP")

    st.markdown(
        """
        This small quant project analyzes how stocks react after **open-market insider purchases**
        using SEC Form 4 data + forward returns from Yahoo Finance.

        **Pipeline:**
        - Load insider buys from your Postgres DB  
        - Identify **large vs. normal** purchases per ticker  
        - Compute **forward returns** (3–30 days)  
        - View summary stats + equity curve  
        """
    )

    # Sidebar parameters
    st.sidebar.header("Parameters")
    min_value_usd = st.sidebar.number_input(
        "Minimum insider purchase size (USD)",
        min_value=1_000.0,
        max_value=2_000_000.0,
        value=10_000.0,
        step=5_000.0,
    )

    horizon = st.sidebar.slider(
        "Forward return horizon (days)",
        3,
        30,
        10,
    )

    quantile = st.sidebar.slider(
        "Quantile for large buys (per ticker)",
        0.5,
        0.95,
        0.75,
    )

    start_date = st.sidebar.date_input("Start date", pd.to_datetime("2024-01-01"))
    end_date = st.sidebar.date_input("End date", pd.to_datetime("2025-01-01"))

    run_button = st.sidebar.button("Run Analysis")

    if not run_button:
        st.info("Set parameters and click **Run Analysis**.")
        return

    with st.spinner("Running analysis..."):
        buys, results, summary, stats = run_pipeline(
            min_value_usd,
            str(start_date),
            str(end_date),
            quantile,
            horizon,
        )

    if results.empty:
        st.warning("No forward returns available for these parameters.")
        return

    ret_col = f"ret_{horizon}d"

    # Summary metrics
    st.subheader("Strategy Summary")

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Trades", stats.get("num_trades", 0))
    colB.metric("Total Return", f"{stats.get('total_return', 0)*100:.2f}%")
    colC.metric("Avg Trade", f"{stats.get('avg_trade_return', 0)*100:.2f}%")
    colD.metric("Hit Rate", f"{stats.get('hit_rate', 0)*100:.1f}%")

    # Large vs normal bar chart
    st.subheader(f"Mean {horizon}-day Return – Large vs. Normal Purchases")

    if not summary.empty:
        fig, ax = plt.subplots()
        ax.bar(summary["size_bucket"], summary["mean"], color=["#4CAF50", "#2196F3"])
        ax.axhline(0, color="black", linewidth=1)
        ax.set_ylabel("Average Return")
        st.pyplot(fig)
    else:
        st.info("Not enough data to generate bucket chart.")

    # Equity curve
    st.subheader("Equity Curve (1 unit per trade)")
    equity = (1 + results[ret_col].dropna()).cumprod().reset_index(drop=True)
    st.line_chart(equity)

    # Table of trades
    st.subheader("Trades Used in Analysis")
    st.dataframe(
        results[
            [
                "ticker",
                "company_name",
                "trade_date",
                "insider_name",
                "insider_role",
                "size_bucket",
                "value_usd",
                ret_col,
            ]
        ].sort_values("trade_date", ascending=False),
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
