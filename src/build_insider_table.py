import pandas as pd
from sqlalchemy import create_engine
from config import DB_URL

engine = create_engine(DB_URL)

def build_insider_transactions():
    query = """
        SELECT
            s.accession_number,
            s.issuer_cik,
            s.issuer_trading_symbol AS ticker,
            s.issuer_name AS company_name,
            s.filing_date,
            n.trans_date AS trade_date,
            r.rptownercik AS insider_cik,
            r.rptownername AS insider_name,
            r.rptowner_relationship AS insider_role,
            n.trans_code AS transaction_type,
            n.trans_shares AS shares,
            n.trans_pricepershare AS price,
            n.shrs_ownd_folwng_trans AS shares_after,
            n.direct_indirect_ownership AS direct_or_indirect
        FROM nonderiv_trans n
        JOIN submission s
          ON n.accession_number = s.accession_number
        LEFT JOIN reportingowner r
          ON n.accession_number = r.accession_number
    """
    df = pd.read_sql(query, engine)
    df["ticker"] = df["ticker"].str.strip().str.upper()
    df["value_usd"] = df["shares"] * df["price"]
    df = df.dropna(subset=["ticker", "trade_date", "shares", "price"])
    df.to_sql("insider_transactions", engine, if_exists="replace", index=False)
    print(f"built insider_transactions with {len(df)} rows")

if __name__ == "__main__":
    build_insider_transactions()
