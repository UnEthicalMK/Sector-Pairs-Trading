import pandas as pd

def generate_pair_signals(
    trading_prices,
    stock1,
    stock2,
    spread_mean,
    spread_std,
    base_price_1,  # Replaced anchor_1
    base_price_2,  # Replaced anchor_2
    entry_threshold=2.0,
    max_holding_days=30
):
    pair_df = pd.DataFrame(index=trading_prices.index)
    pair_df["stock1"] = trading_prices[stock1]
    pair_df["stock2"] = trading_prices[stock2]

    # -----------------------------
    # Continuous Normalization
    # -----------------------------
    # By dividing by the raw price from Day 0 of the formation window,
    # the normalized path is 100% continuous and preserves all overnight gaps.
    pair_df["norm1"] = pair_df["stock1"] / base_price_1
    pair_df["norm2"] = pair_df["stock2"] / base_price_2
    pair_df["spread"] = pair_df["norm1"] - pair_df["norm2"]

    upper_band = spread_mean + (entry_threshold * spread_std)
    lower_band = spread_mean - (entry_threshold * spread_std)

    # -----------------------------
    # State Machine Variables
    # -----------------------------
    position = 0
    holding_days = 0
    cooldown_days = 5
    cooldown_counter = 0
    
    # Use a high-speed Python list to track state instead of DataFrame .iloc
    position_history = [0] 

    for i in range(1, len(pair_df) - 1):
        spread_today = pair_df["spread"].iloc[i]
        
        if cooldown_counter > 0:
            cooldown_counter -= 1

        # --- No Active Trade ---
        if position == 0 and cooldown_counter == 0:
            if spread_today > upper_band:
                position = -1
                holding_days = 0
            elif spread_today < lower_band:
                position = 1
                holding_days = 0

        # --- Active Trade ---
        elif position != 0:
            holding_days += 1
            previous_spread = pair_df["spread"].iloc[i - 1]

            # Trigger 1: Touch the mean
            mean_reverted = abs(spread_today - spread_mean) < (0.25 * spread_std)
            
            # Trigger 2: Violent gap past the mean (sign change relative to mean)
            spread_relative_today = spread_today - spread_mean
            spread_relative_prev = previous_spread - spread_mean
            crossed_mean = (spread_relative_today * spread_relative_prev) < 0

            # Trigger 3: Catastrophic divergence
            stop_loss = abs(spread_today - spread_mean) > (4 * spread_std)
            
            # Trigger 4: Time decay
            timeout = holding_days >= max_holding_days

            if mean_reverted or crossed_mean or stop_loss or timeout:
                position = 0
                holding_days = 0
                cooldown_counter = cooldown_days

        # Append state to fast list
        position_history.append(position)

    # Force liquidation on the final day of the trading window
    position_history.append(0)

    # Assign list to DataFrame in one single vectorized operation
    pair_df["position"] = position_history

    return pair_df