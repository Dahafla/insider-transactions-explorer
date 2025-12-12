import math
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text
from config import DB_URL

engine = create_engine(DB_URL)

# Customize these if you want
START = "2020-01-01"
END = "2025-01-01"
BATCH_SIZE = 50  # number of tickers per batch


def ensure_daily_prices_table():
    ddl = """
    CREATE TABLE IF NOT EXISTS daily_prices (
        ticker TEXT NOT NULL,
        trade_date DATE NOT NULL,
        adj_close DOUBLE PRECISION,
        PRIMARY KEY (ticker, trade_date)
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def get_all_tickers():
    query = "SELECT DISTINCT ticker FROM insider_transactions"
    df = pd.read_sql(query, engine)
    tickers = sorted(df["ticker"].dropna().unique().tolist())
    print(f"Found {len(tickers)} distinct tickers in insider_transactions")
    return tickers


def download_and_store_batch(tickers_batch, start, end, batch_index, total_batches):
    print(f"\n📥 Batch {batch_index}/{total_batches} – {len(tickers_batch)} tickers")

    # yfinance multi-ticker download
    try:
        data = yf.download(
            tickers_batch,
            start=start,
            end=end,
            auto_adjust=False,
            group_by="ticker",
            progress=False,
            threads=False,  # avoid OS thread explosion
        )
    except Exception as e:
        print(f"⚠️ Failed to download batch {batch_index}: {e}")
        return

    if data is None or data.empty:
        print(f"⚠️ No data returned for batch {batch_index}")
        return

    with engine.begin() as conn:
        # If you want to make reruns clean, you can delete existing rows for this batch:
        conn.execute(
            text("DELETE FROM daily_prices WHERE ticker = ANY(:tickers)"),
            {"tickers": tickers_batch},
        )

        # Case 1: single ticker → columns are simple, not MultiIndex
        if not isinstance(data.columns, pd.MultiIndex) and len(tickers_batch) == 1:
            t = tickers_batch[0]
            df = data.reset_index()

            if "Adj Close" in df.columns:
                price_col = "Adj Close"
            elif "Close" in df.columns:
                price_col = "Close"
            else:
                print(f"⚠️ {t}: no usable price column. Columns: {list(df.columns)}")
                return

            df = df[["Date", price_col]].rename(columns={
                "Date": "trade_date",
                price_col: "adj_close",
            })
            df["ticker"] = t
            df.to_sql("daily_prices", conn, if_exists="append", index=False)
            print(f"✅ Stored {t} ({len(df)} rows)")
            return

        # Case 2: multi-ticker → MultiIndex columns: (ticker, field)
        if isinstance(data.columns, pd.MultiIndex):
            for t in tickers_batch:
                if t not in data.columns.get_level_values(0):
                    print(f"⚠️ No data for {t} in this batch")
                    continue

                df_t = data[t].reset_index()

                if "Adj Close" in df_t.columns:
                    price_col = "Adj Close"
                elif "Close" in df_t.columns:
                    price_col = "Close"
                else:
                    print(f"⚠️ {t}: no usable price column. Columns: {list(df_t.columns)}")
                    continue

                df_t = df_t[["Date", price_col]].rename(columns={
                    "Date": "trade_date",
                    price_col: "adj_close",
                })
                df_t["ticker"] = t

                if df_t.empty:
                    print(f"⚠️ {t}: empty price frame")
                    continue

                df_t.to_sql("daily_prices", conn, if_exists="append", index=False)
                print(f"✅ Stored {t} ({len(df_t)} rows)")
        else:
            print(f"⚠️ Unexpected data shape for batch {batch_index}: {data.shape}")


def main():
    ensure_daily_prices_table()
    tickers = get_all_tickers()

    if not tickers:
        print("No tickers found in insider_transactions. Did you run build_insider_table.py?")
        return

    total = len(tickers)
    total_batches = math.ceil(total / BATCH_SIZE)

    for i in range(total_batches):
        start_idx = i * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total)
        batch = tickers[start_idx:end_idx]
        download_and_store_batch(batch, START, END, i + 1, total_batches)

    print("\n✅ Finished preloading daily prices for all tickers.")


if __name__ == "__main__":
    main()