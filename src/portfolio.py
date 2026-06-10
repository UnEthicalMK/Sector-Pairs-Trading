import numpy as np
import pandas as pd


def backtest_pair(signal_df, transaction_cost=0.001):
    """
    Backtest a single pair, adjusted for time-shifting and dual-leg costs.
    """
    df = signal_df.copy()

    # Daily returns for each asset
    df["ret1"] = df["stock1"].pct_change().fillna(0)
    df["ret2"] = df["stock2"].pct_change().fillna(0)

    # 1. SHIFT FIX: The position held today was decided at yesterday's close.
    # This completely eliminates lookahead bias.
    df["actual_position"] = df["position"].shift(1).fillna(0)

    # 2. LEVERAGE FIX: Divide by 2 to account for capital split across two legs.
    df["pair_return"] = np.where(
        df["actual_position"] == 1,
        (df["ret1"] - df["ret2"]) / 2.0,
        np.where(
            df["actual_position"] == -1,
            (df["ret2"] - df["ret1"]) / 2.0,
            0.0
        )
    )

    # 3. COST FIX: Calculate when a trade is executed based on the RAW signal
    df["trade_flag"] = df["position"].diff().abs().fillna(0)

    # Multiply by 2 because opening/closing a pair requires 2 stock transactions
    df["cost"] = df["trade_flag"] * transaction_cost * 2

    # Calculate final net return and equity curve
    df["net_return"] = df["pair_return"] - df["cost"]
    df["equity_curve"] = (1 + df["net_return"]).cumprod()

    return df


def aggregate_pair_returns(pair_results):
    """
    Equal-weight all pair returns across the portfolio.
    """
    portfolio = pd.DataFrame()

    for i, result in enumerate(pair_results):
        portfolio[f"pair_{i}"] = result["net_return"]

    portfolio = portfolio.fillna(0)

    # Averages returns across all active/inactive pairs 
    # (Assuming equal capital allocation per pair slot)
    portfolio["portfolio_return"] = portfolio.mean(axis=1)
    portfolio["equity_curve"] = (1 + portfolio["portfolio_return"]).cumprod()

    return portfolio


def combine_window_portfolios(portfolios):
    """
    Combine rolling-window portfolios safely.
    """
    combined = pd.concat(portfolios, axis=0)

    # Drop overlapping days, keeping the fresher formation data ("last" is usually safer 
    # than "first" if windows overlap, but first is fine for strict walk-forwards)
    combined = (
        combined
        .sort_index()
        .loc[~combined.index.duplicated(keep="first")]
    )

    # Recalculate global cumprod after stitching the daily returns together
    combined["equity_curve"] = (1 + combined["portfolio_return"]).cumprod()

    return combined