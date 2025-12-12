# src/run_analysis.py

import os
import pandas as pd
import matplotlib.pyplot as plt

from quant_insider_core import (
    load_insider_buys,
    tag_large_buys,
    compute_forward_returns,
    summarize_returns,
)

# ---------------------- PARAMETERS ----------------------
MIN_VALUE = 10_000
START = "2024-01-01"
END = "2025-01-01"
QUANTILE = 0.75
HORIZON = 10
OUTPUT_DIR = "charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_bucket_bar(summary: pd.DataFrame, horizon: int, output_path: str):
    order = ["normal_buy", "large_buy"]
    summary = summary.set_index("size_bucket")
    summary = summary.reindex(order).dropna().reset_index()

    labels = summary["size_bucket"].values
    counts = summary["count"].values

    # plot in percent for readability
    means_pct = (summary["mean"] * 100).values

    # optional uncertainty: standard error if std exists
    yerr = None
    if "std" in summary.columns:
        std_pct = (summary["std"] * 100).values
        yerr = std_pct / (counts ** 0.5)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, means_pct, yerr=yerr, capsize=4 if yerr is not None else 0)
    ax.axhline(0, linewidth=1)

    ax.set_ylabel(f"Mean {horizon}-Day Return (%)")
    ax.set_title(f"Mean {horizon}-Day Forward Return\nLarge vs Normal Insider Buys")

    for x, y, n in zip(labels, means_pct, counts):
        va = "bottom" if y >= 0 else "top"
        ax.text(x, y, f"n={n}", ha="center", va=va, fontsize=9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def equity_by_calendar(results: pd.DataFrame, horizon: int):
    col = f"ret_{horizon}d"
    df = results.dropna(subset=[col]).copy()

    # Use trade_date + horizon as "exit date" for the trade
    df["exit_date"] = df["trade_date"] + pd.Timedelta(days=horizon)

    # Average return of all trades ending on the same date
    daily = (
        df.groupby("exit_date")[col]
        .mean()
        .sort_index()
    )

    equity = (1 + daily).cumprod()
    return equity

def max_drawdown(equity: pd.Series) -> float:
    roll_max = equity.cummax()
    drawdown = (equity / roll_max) - 1.0
    return drawdown.min()  # negative


def plot_equity_curve(results: pd.DataFrame, horizon: int, output_path: str):
    col = f"ret_{horizon}d"
    rets = results[col]
    equity = equity_by_calendar(results, HORIZON)
    if equity.empty:
        return

    mdd = max_drawdown(equity)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(equity.index, equity.values)
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Return")
    ax.set_title("Equity Curve – Calendar-Time Strategy")
    ax.text(
    0.01, 0.02, f"MDD: {mdd:.2%}",
    transform=ax.transAxes, ha="left", va="bottom", fontsize=9
)
    ax.grid(True, linewidth=0.5)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_return_distribution(results: pd.DataFrame, horizon: int, output_path: str):
    col = f"ret_{horizon}d"
    rets = results[col].dropna()

    rets_pct = rets * 100
    lo, hi = rets_pct.quantile([0.01, 0.99])


    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(rets_pct, bins=40)
    ax.axvline(rets_pct.mean(), linestyle="--", linewidth=1)
    
    ax.set_xlim(lo, hi)
    ax.set_xlabel(f"{horizon}-Day Return (%)")
    ax.set_ylabel("Number of Trades")
    ax.set_title(f"Distribution of {horizon}-Day Returns")
    ax.legend()

    try:
        fig.tight_layout()
    except:
        plt.subplots_adjust(top=0.88)

    fig.savefig(output_path)
    plt.close(fig)


def main():
    print("Loading insider buy data...")
    buys = load_insider_buys(
        min_value_usd=MIN_VALUE,
        start_date=START,
        end_date=END,
    )

    if buys.empty:
        print("No insider buys found for this filter.")
        return

    print(f"Loaded {len(buys)} insider purchase records.")

    print("Tagging large vs normal buys...")
    buys = tag_large_buys(buys, QUANTILE)

    print("Computing forward returns...")
    results = compute_forward_returns(buys, HORIZON)

    if results.empty:
        print("No valid forward returns. Try different parameters.")
        return

    summary, stats = summarize_returns(results, HORIZON)

    print("\n===== SUMMARY =====")
    print(summary)
    print("\n===== STATS =====")
    for k, v in stats.items():
        print(f"{k}: {v}")

    # Plots
    plot_bucket_bar(summary, HORIZON, f"{OUTPUT_DIR}/large_vs_normal.png")
    plot_equity_curve(results, HORIZON, f"{OUTPUT_DIR}/equity_curve.png")
    plot_return_distribution(results, HORIZON, f"{OUTPUT_DIR}/return_dist.png")

    # Save raw data too
    results.to_csv(f"{OUTPUT_DIR}/results.csv", index=False)
    summary.to_csv(f"{OUTPUT_DIR}/summary.csv", index=False)

    print("\nCharts and CSVs saved in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
