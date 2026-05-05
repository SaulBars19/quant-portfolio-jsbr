import pandas as pd
import requests
import certifi
from io import StringIO


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_tables(url):
    response = requests.get(url, headers=HEADERS, verify=certifi.where(), timeout=20)
    response.raise_for_status()
    return pd.read_html(StringIO(response.text))


def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = fetch_tables(url)
    table = tables[0]

    return (
        table["Symbol"]
        .dropna()
        .astype(str)
        .str.replace(".", "-", regex=False)
        .tolist()
    )


def get_nasdaq100_tickers():
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = fetch_tables(url)

    for table in tables:
        if "Ticker" in table.columns:
            return (
                table["Ticker"]
                .dropna()
                .astype(str)
                .str.replace(".", "-", regex=False)
                .tolist()
            )

    return []


def get_swiss_tickers():
    url = "https://en.wikipedia.org/wiki/Swiss_Market_Index"
    tables = fetch_tables(url)

    for table in tables:
        if "Symbol" in table.columns:
            tickers = table["Symbol"].dropna().astype(str).tolist()
            return [t if t.endswith(".SW") else t + ".SW" for t in tickers]

    return []


def get_dax_tickers():
    url = "https://en.wikipedia.org/wiki/DAX"
    tables = fetch_tables(url)

    for table in tables:
        if "Ticker" in table.columns or "Symbol" in table.columns:
            col = [c for c in table.columns if "Ticker" in c or "Symbol" in c][0]
            tickers = table[col].dropna().astype(str).tolist()
            return [t + ".DE" if ".DE" not in t else t for t in tickers]

    return []


def get_china_hk_tickers():
    url = "https://en.wikipedia.org/wiki/Hang_Seng_Index"
    tables = fetch_tables(url)

    for table in tables:
        possible_cols = [c for c in table.columns if "Ticker" in str(c) or "Symbol" in str(c)]

        if possible_cols:
            col = possible_cols[0]
            tickers = table[col].dropna().astype(str).tolist()

            clean_tickers = []
            for t in tickers:
                t = t.strip()
                if not t.endswith(".HK"):
                    t = t + ".HK"
                clean_tickers.append(t)

            return clean_tickers

    return []


def build_universe():
    tickers = []
    tickers += get_sp500_tickers()
    tickers += get_nasdaq100_tickers()
    #tickers += get_swiss_tickers()
    #tickers += get_dax_tickers()
    #tickers += get_china_hk_tickers() #Unlock the tickers if needed.

    return sorted(list(set(tickers)))


if __name__ == "__main__":
    universe = build_universe()
    print(f"Universe size: {len(universe)}")
    print(universe[:20]) #:20 shows the first 20 data elements.