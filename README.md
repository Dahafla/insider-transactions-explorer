# Insider Trading Reaction Model

**A Quantitative Event-Study of Forward Returns After Insider Purchases**

Built with **Python, SQL, Yahoo Finance, and Matplotlib**

This project analyzes how stocks react after open-market insider purchases (Form 4 filings).
Instead of treating all insider buys the same, the system:

- Classifies insider purchases into large vs normal buckets
- Computes 10-day forward returns
- Builds a calendar-time equity curve
- Generates a distribution analysis across thousands of insider events

# Visualizations & Interpretation

## 1. Large vs Normal Insider Buys — Mean 10-Day Forward Returns

![Daily SLeep Index](charts/large_vs_normal.png)

**Interpretation:**

- Large insider buys slightly outperform normal buys
- Suggests insiders who buy more than usual for their own stock tend to be directionally correct
- Difference is small but statistically meaningful given large sample size (n ≈ 16,000)

## 2. 10-Day Return Distribution

![Daily SLeep Index](charts/return_dist.png)

**Interpretation:**

- Distribution is centered slightly above zero → insider buys are mildly bullish on average
- Right-skewed tail → some insider buys capture big positive moves
- Left tail exists → insiders are not perfect and sometimes buy ahead of declines
- Supports the idea that insider activity is a weak but exploitable signal

## 3. Calendar-Time Equity Curve

![Daily SLeep Index](charts/equity_curve.png)

**Interpretation:**

- Curve shows periods of flat performance followed by strong uptrends
- Indicates episodic alpha, likely regime-dependent
- MDD around –67%, suggesting high volatility
- Insider buy signals alone are not a standalone trading system, but useful as a feature

# Key Findings

- **Large insider purchases outperform normal buys**, indicates insider conviction matters.
- The **distribution of forward returns is right-skewed**, showing occasional large gains.
- A **raw insider-buy strategy is volatile** with deep drawdowns.
- Signal strength appears **regime-dependent** (some periods work extremely well).
- Insider data is likely best used as a **factor or overlay**, not a standalone model.
- Academic literature supports this: insider trading signals generate alpha when combined with fundamentals, momentum, or cluster activity.

# Project Architecture

```bash
.
├── data/2024Q*/                 # Raw SEC TSV folders
├── src/
│   ├── load_raw.py              # Ingest SEC TSVs
│   ├── build_insider_table.py   # Build unified insider table
│   ├── preload_prices.py        # Download & insert price data
│   ├── quant_insider_core.py    # Core event + return logic
│   ├── run_analysis.py          # Generates results + charts
├── charts/
│   ├── large_vs_normal.png
│   ├── return_dist.png
│   ├── equity_curve.png
│   ├── results.csv
│   └── summary.csv
└── README.md
```
