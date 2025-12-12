# load_raw.py
import os
import glob
import pandas as pd
from sqlalchemy import create_engine
from config import DB_URL

engine = create_engine(DB_URL)


def parse_date(series: pd.Series) -> pd.Series:
    """
    Parse SEC-style dates like '01-Jan-2024'.
    """
    return pd.to_datetime(series, format="%d-%b-%Y", errors="coerce")


def load_submission():
    for folder in glob.glob("data/2024Q*"):
        path = os.path.join(folder, "SUBMISSION.TSV")
        if not os.path.exists(path):
            print(f"NO SUBMISSION.TSV in {folder}")
            continue

        print(f"Loading {path}")
        df = pd.read_csv(path, sep="\t", dtype=str)

        rename_map = {
            "ACCESSION_NUMBER": "accession_number",
            "FILING_DATE": "filing_date",
            "PERIOD_OF_REPORT": "period_of_report",
            "ISSUERCIK": "issuer_cik",
            "ISSUERNAME": "issuer_name",
            "ISSUERTRADINGSYMBOL": "issuer_trading_symbol",
        }
        df = df[rename_map.keys()].rename(columns=rename_map)

        df["filing_date"] = parse_date(df["filing_date"])
        df["period_of_report"] = parse_date(df["period_of_report"])

        df.to_sql("submission", engine, if_exists="append", index=False)


def load_reportingowner():
    for folder in glob.glob("data/2024Q*"):
        path = os.path.join(folder, "REPORTINGOWNER.TSV")
        if not os.path.exists(path):
            print(f"NO REPORTINGOWNER in {folder}")
            continue

        print(f"Loading {path}")
        df = pd.read_csv(path, sep="\t", dtype=str)

        rename_map = {
            "ACCESSION_NUMBER": "accession_number",
            "RPTOWNERCIK": "rptownercik",
            "RPTOWNERNAME": "rptownername",
            "RPTOWNER_RELATIONSHIP": "rptowner_relationship",
            "RPTOWNER_TITLE": "rptowner_title",
        }
        df = df[rename_map.keys()].rename(columns=rename_map)

        df.columns = df.columns.str.lower()
        df.to_sql("reportingowner", engine, if_exists="append", index=False)


def load_nonderiv_trans():
    for folder in glob.glob("data/2024Q*"):
        path = os.path.join(folder, "NONDERIV_TRANS.TSV")
        if not os.path.exists(path):
            print(f"NO NONDERIV_TRANS in {folder}")
            continue

        print(f"Loading {path}")
        df = pd.read_csv(path, sep="\t", dtype=str)

        rename_map = {
            "ACCESSION_NUMBER": "accession_number",
            "NONDERIV_TRANS_SK": "nonderiv_trans_sk",
            "SECURITY_TITLE": "security_title",
            "TRANS_DATE": "trans_date",
            "TRANS_FORM_TYPE": "trans_form_type",
            "TRANS_CODE": "trans_code",
            "EQUITY_SWAP_INVOLVED": "equity_swap_involved",
            "TRANS_TIMELINESS": "trans_timeliness",
            "TRANS_SHARES": "trans_shares",
            "TRANS_PRICEPERSHARE": "trans_pricepershare",
            "TRANS_ACQUIRED_DISP_CD": "trans_acquired_disp_cd",
            "SHRS_OWND_FOLWNG_TRANS": "shrs_ownd_folwng_trans",
            "DIRECT_INDIRECT_OWNERSHIP": "direct_indirect_ownership",
        }
        df = df[rename_map.keys()].rename(columns=rename_map)

        df.columns = df.columns.str.lower()

        df["trans_date"] = parse_date(df["trans_date"])
        df["trans_shares"] = pd.to_numeric(df["trans_shares"], errors="coerce")
        df["trans_pricepershare"] = pd.to_numeric(
            df["trans_pricepershare"], errors="coerce"
        )
        df["shrs_ownd_folwng_trans"] = pd.to_numeric(
            df["shrs_ownd_folwng_trans"], errors="coerce"
        )

        df.to_sql("nonderiv_trans", engine, if_exists="append", index=False)


if __name__ == "__main__":
    load_submission()
    load_reportingowner()
    load_nonderiv_trans()
    print("Loaded all 2024Q* raw tables")
