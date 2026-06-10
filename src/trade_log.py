import pandas as pd
import numpy as np

def trade_statistics(trade_log):
    if len(trade_log) == 0:
        return pd.Series(
            {
                "Total Trades": 0,
                "Win Rate": 0.0,
                "Average Return": 0.0,
                "Average Holding Days": 0.0
            }
        )

    return pd.Series(
        {
            "Total Trades": len(trade_log),
            "Win Rate": (trade_log["return"] > 0).mean(),
            "Average Return": trade_log["return"].mean(),
            "Average Holding Days": trade_log["holding_days"].mean()
        }
    )

def extract_trade_log(signal_df, pair_name):
    """
    Extract completed trades from a pair, accounting for direct position 
    flips and utilizing exact localized compounding for returns.
    """
    trades = []

    # Fast numpy arrays for O(1) lookups
    positions = signal_df["position"].values
    net_returns = signal_df["net_return"].values
    dates = signal_df.index

    in_trade = False
    entry_idx = None
    direction = None

    for i in range(1, len(positions)):
        prev_pos = positions[i - 1]
        curr_pos = positions[i]

        # Trigger whenever the state machine changes
        if curr_pos != prev_pos:
            
            # 1. Close existing trade if one is active
            if prev_pos != 0 and in_trade:
                exit_idx = i
                
                # Isolate the exact daily returns for this specific holding period.
                # We start at entry_idx + 1 because the position taken at the end of 
                # Day T earns its first return on Day T+1.
                trade_daily_returns = net_returns[entry_idx + 1 : exit_idx + 1]
                
                # Geometrically compound the daily returns
                trade_return = np.prod(1 + trade_daily_returns) - 1
                
                holding_days = (dates[exit_idx] - dates[entry_idx]).days
                
                trades.append({
                    "pair": pair_name,
                    "direction": direction,
                    "entry_date": dates[entry_idx],
                    "exit_date": dates[exit_idx],
                    "holding_days": holding_days,
                    "return": trade_return
                })
                in_trade = False

            # 2. Open a new trade if the new state isn't cash (0)
            if curr_pos != 0:
                in_trade = True
                entry_idx = i
                direction = curr_pos

    # Convert to DataFrame
    df_trades = pd.DataFrame(trades)
    
    # Return empty DataFrame with correct columns if no trades occurred
    if df_trades.empty:
        return pd.DataFrame(columns=[
            "pair", "direction", "entry_date", "exit_date", "holding_days", "return"
        ])
        
    return df_trades