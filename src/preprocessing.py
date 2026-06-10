import pandas as pd
import numpy as np


def normalize_prices(prices):
    """
    Normalize each stock so that all series start at 1.0.
    Explicitly aligns along columns to prevent alignment bugs.
    """
    if prices.empty:
        return prices
    # Explicitly define axis=1 (columns) to secure the structural operation
    return prices.div(prices.iloc[0], axis=1)


def create_return_index(prices):
    """
    Create cumulative return indices.
    Starts every stock at 1.0 and compounds returns safely, 
    preventing mid-series NaN propagation corruption.
    """
    if prices.empty:
        return prices

    returns = prices.pct_change()
    
    # FIX: Fill the first row's NaN and any intermediate trading halts with 0.0
    # This prevents cumprod() from propagating NaNs to the end of the dataset.
    clean_returns = returns.fillna(0.0)

    return (1 + clean_returns).cumprod()


def calculate_spread(series1, series2):
    """
    Compute spread between two normalized series.
    """
    return series1 - series2


def spread_statistics(spread):
    """
    Compute historical spread statistics during the formation period.
    """
    # Using ddof=1 (default) ensures an unbiased sample standard deviation estimate
    mean_spread = spread.mean()
    std_spread = spread.std()

    return mean_spread, std_spread