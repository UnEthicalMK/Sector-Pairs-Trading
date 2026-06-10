from itertools import combinations
from collections import defaultdict
import numpy as np
import pandas as pd

from src.sector_map import SECTOR_MAP


def compute_ssd(series1, series2):
    return np.sum((series1 - series2) ** 2)


def rank_pairs_by_sector(normalized_prices):
    """
    Groups tickers by sector first to reduce algorithmic complexity 
    from O(N^2) global combinations to localized cluster combinations.
    """
    results = []
    tickers = normalized_prices.columns

    # Step 1: Group tickers by their sector first (Prevents O(N^2) explosion)
    sector_buckets = defaultdict(list)
    for ticker in tickers:
        sector = SECTOR_MAP.get(ticker)
        if sector is not None:  # Fixes the None == None edge case bug
            sector_buckets[sector].append(ticker)

    # Step 2: Only calculate combinations within identical sectors
    for sector, sector_tickers in sector_buckets.items():
        if len(sector_tickers) < 2:
            continue
            
        for stock1, stock2 in combinations(sector_tickers, 2):
            ssd = compute_ssd(
                normalized_prices[stock1],
                normalized_prices[stock2]
            )

            results.append(
                {
                    "stock_1": stock1,
                    "stock_2": stock2,
                    "sector": sector,
                    "ssd": ssd
                }
            )

    if not results:
        return pd.DataFrame(columns=["stock_1", "stock_2", "sector", "ssd"])

    results = pd.DataFrame(results)
    return results.sort_values("ssd", ascending=True).reset_index(drop=True)


def select_top_pairs(normalized_prices, pairs_per_sector=1):
    """
    Selects the top N pairs per sector to guarantee market-wide
    diversification across your expanded universe.
    """
    ranked_pairs = rank_pairs_by_sector(normalized_prices)
    
    if ranked_pairs.empty:
        return ranked_pairs

    # Group by sector and take the top N performing pairs for each industry
    top_pairs = (
        ranked_pairs
        .groupby("sector")
        .head(pairs_per_sector)
        .reset_index(drop=True)
    )
    
    return top_pairs


def compute_pair_spread_statistics(normalized_prices, selected_pairs):
    stats = []

    for _, row in selected_pairs.iterrows():
        stock1 = row["stock_1"]
        stock2 = row["stock_2"]

        spread = (
            normalized_prices[stock1] 
            - normalized_prices[stock2]
        )

        stats.append(
            {
                "stock_1": stock1,
                "stock_2": stock2,
                "sector": row["sector"],
                "ssd": row["ssd"],
                "spread_mean": spread.mean(),
                "spread_std": spread.std(),

                # Save formation anchors to correctly orient trading period entry
                "anchor_1": normalized_prices[stock1].iloc[-1],
                "anchor_2": normalized_prices[stock2].iloc[-1]
            }
        )

    return pd.DataFrame(stats)