DROP TABLE IF EXISTS insider_transactions CASCADE;

CREATE TABLE insider_transactions (
    id SERIAL PRIMARY KEY,
    accession_number VARCHAR(32),
    issuer_cik VARCHAR(20),
    ticker VARCHAR(16),
    company_name TEXT,
    filing_date DATE,
    trade_date DATE,
    insider_cik VARCHAR(20),
    insider_name TEXT,
    insider_role TEXT,
    transaction_type VARCHAR(8),
    shares NUMERIC,
    price NUMERIC,
    value_usd NUMERIC,
    shares_after NUMERIC,
    direct_or_indirect VARCHAR(4)
);

CREATE TABLE IF NOT EXISTS daily_prices (
    ticker TEXT NOT NULL,
    trade_date DATE NOT NULL,
    adj_close DOUBLE PRECISION,
    PRIMARY KEY (ticker, trade_date)
);