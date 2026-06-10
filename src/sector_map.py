import pandas as pd
import os
import json

def get_sp500_sector_mapping(cache_file="data/sp500_sectors.json"):
    """
    Returns S&P 500 sector mappings, utilizing a local cache to prevent 
    redundant network I/O and Wikipedia rate-limiting.
    """
    # Create the data directory if it doesn't exist
    if os.path.dirname(cache_file):
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)

    # 1. Check if we already have the data cached locally
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            data = json.load(f)
            return data["sector_to_tickers"], data["ticker_to_sector"]

    # 2. If no cache exists, scrape the live web data
    print("Scraping S&P 500 data from Wikipedia...")
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    
    # FIX: Disguise the Python script as a standard Google Chrome web browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Pass the headers into pandas using storage_options
    df = pd.read_html(url, storage_options=headers)[0]

    # Clean symbols for Yahoo Finance format
    df["Symbol"] = df["Symbol"].str.replace(".", "-", regex=False)

    sector_to_tickers = df.groupby("GICS Sector")["Symbol"].apply(list).to_dict()
    ticker_to_sector = df.set_index("Symbol")["GICS Sector"].to_dict()

    # 3. Save to local cache for all future runs
    with open(cache_file, "w") as f:
        json.dump({
            "sector_to_tickers": sector_to_tickers,
            "ticker_to_sector": ticker_to_sector
        }, f, indent=4)

    return sector_to_tickers, ticker_to_sector


# =====================================================================
# Initialize SECTOR_MAP globally so src.pair_selection can import it
# =====================================================================
try:
    _, SECTOR_MAP = get_sp500_sector_mapping()
except Exception as e:
    print(f"Warning: Could not initialize global SECTOR_MAP automatically: {e}")
    SECTOR_MAP = {}