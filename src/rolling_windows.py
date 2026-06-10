import pandas as pd

def generate_windows(
    prices,
    formation_days=252,
    trading_days=126,
    step_size=126
):
    """
    Generate rolling formation/trading windows, capturing the final 
    partial window and explicitly logging date metadata.
    """
    if len(prices) <= formation_days:
        raise ValueError(
            f"Insufficient data. Need > {formation_days} days, got {len(prices)}."
        )

    windows = []
    start = 0
    window_id = 1

    while True:
        formation_start = start
        formation_end = formation_start + formation_days
        trading_start = formation_end

        # Break ONLY if we don't even have 1 day of out-of-sample data left
        if trading_start >= len(prices):
            break

        # Capping the trading end to the dataframe length ensures we don't 
        # drop the most recent, currently-active market data.
        trading_end = min(trading_start + trading_days, len(prices))

        formation_data = prices.iloc[formation_start:formation_end]
        trading_data = prices.iloc[trading_start:trading_end]

        windows.append(
            {
                "window_id": window_id,
                "formation": formation_data,
                "trading": trading_data,
                
                # Explicit metadata logging for easy downstream debugging
                "formation_start_date": formation_data.index[0],
                "formation_end_date": formation_data.index[-1],
                "trading_start_date": trading_data.index[0],
                "trading_end_date": trading_data.index[-1]
            }
        )

        start += step_size
        window_id += 1

    return windows