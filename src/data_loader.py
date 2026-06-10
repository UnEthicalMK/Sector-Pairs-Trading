import yfinance as yf
import pandas as pd

def load_prices(tickers, start_date, end_date):
    """
    Download raw daily price data.
    """
    data = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False
    )
    
    # Handle yfinance multi-index column quirks
    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        prices = data
        
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    return prices


def remove_illiquid_stocks(prices, required_days=378):
    """
    Remove stocks with missing observations or insufficient history.
    """
    # Drop stocks that have NaN values (didn't trade every day)
    clean_prices = prices.dropna(axis=1)
    
    # Drop stocks that don't have enough history for the full window
    if len(clean_prices) < required_days:
        raise ValueError(f"Insufficient data. Expected at least {required_days} rows, got {len(clean_prices)}.")
        
    return clean_prices


def split_formation_trading(prices, formation_days=252, trading_days=126):
    """
    Split data into formation and trading windows.
    """
    total_required = formation_days + trading_days
    
    # Strict validation check
    if len(prices) < total_required:
        raise ValueError(f"Dataframe length ({len(prices)}) is less than required ({total_required})")

    formation_prices = prices.iloc[:formation_days]
    trading_prices = prices.iloc[formation_days:total_required]

    return formation_prices, trading_prices