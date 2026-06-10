import os
import matplotlib.pyplot as plt
import pandas as pd

from src.data_loader import load_prices
from src.preprocessing import normalize_prices
from src.pair_selection import select_top_pairs, compute_pair_spread_statistics
from src.signal_generation import generate_pair_signals
from src.portfolio import backtest_pair, aggregate_pair_returns, combine_window_portfolios
from src.performance import summarize_performance
from src.rolling_windows import generate_windows
from src.trade_log import extract_trade_log, trade_statistics
from src.sector_map import get_sp500_sector_mapping

# Fetch the sector mapping (Using our cached version!)
sector_to_tickers, ticker_to_sector = get_sp500_sector_mapping()


# ----------------------------------
# CONFIG
# ----------------------------------
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "META", "NVDA",
    "JPM", "BAC", "XOM", "CVX", "WMT", "TGT", "PG"
]

PAIRS_PER_SECTOR = 2  
TRANSACTION_COST = 0.0006  # 6 bps total friction


# ----------------------------------
# LOAD DATA
# ----------------------------------
prices = load_prices(
    tickers=TICKERS,
    start_date="2018-01-01",
    end_date="2024-01-01"
)

print(f"Loaded {len(prices)} observations.")


# ----------------------------------
# GENERATE ROLLING WINDOWS
# ----------------------------------
windows = generate_windows(
    prices=prices,
    formation_days=252,
    trading_days=126,
    step_size=126
)

print(f"Generated {len(windows)} rolling windows.")

all_portfolios = []
all_trades = []

# ----------------------------------
# LOOP THROUGH WINDOWS
# ----------------------------------
for window_number, window in enumerate(windows, start=1):
    
    print(f"\nProcessing Window {window_number}")

    formation_prices = window["formation"]
    trading_prices = window["trading"]

    normalized_formation = normalize_prices(formation_prices)

    # Use the refactored sector-diversified selection
    top_pairs = select_top_pairs(
        normalized_formation,
        pairs_per_sector=PAIRS_PER_SECTOR
    )

    pair_stats = compute_pair_spread_statistics(
        normalized_formation,
        top_pairs
    )

    pair_results = []

    # ----------------------------------
    # INDIVIDUAL PAIR EXECUTION
    # ----------------------------------
    for _, pair in pair_stats.iterrows():
        stock1 = pair["stock_1"]
        stock2 = pair["stock_2"]
        
        # Dynamically extract Day 0 raw prices to fix the overnight gap leak
        base_price_1 = formation_prices[stock1].iloc[0]
        base_price_2 = formation_prices[stock2].iloc[0]

        signals = generate_pair_signals(
            trading_prices=trading_prices,
            stock1=stock1,
            stock2=stock2,
            spread_mean=pair["spread_mean"],
            spread_std=pair["spread_std"],
            base_price_1=base_price_1, 
            base_price_2=base_price_2, 
            entry_threshold=2.0
        )

        result = backtest_pair(
            signals,
            transaction_cost=TRANSACTION_COST
        )

        pair_name = f"{stock1}-{stock2}"
        
        trades = extract_trade_log(result, pair_name)
        all_trades.append(trades)
        
        pair_results.append(result)

    # Aggregate all pairs into one window portfolio
    if pair_results:
        portfolio = aggregate_pair_returns(pair_results)
        all_portfolios.append(portfolio)
    else:
        print(f"  -> No valid pairs found in Window {window_number}")


# ----------------------------------
# COMBINE WINDOWS & FINALIZE
# ----------------------------------
master_portfolio = combine_window_portfolios(all_portfolios)

# Safety check for empty trades
valid_trades = [df for df in all_trades if not df.empty]
if valid_trades:
    trade_log = pd.concat(valid_trades, ignore_index=True)
else:
    trade_log = pd.DataFrame()


# ----------------------------------
# PERFORMANCE
# ----------------------------------
performance_input = master_portfolio.rename(
    columns={"portfolio_return": "net_return"}
)

summary = summarize_performance(performance_input)

# GUARANTEE DIRECTORY EXISTS
os.makedirs("data", exist_ok=True)

if not trade_log.empty:
    # UPDATED PATH: Saved inside the data/ directory
    trade_log.to_csv("data/trade_log.csv", index=False)
    stats = trade_statistics(trade_log)
else:
    stats = "No trades executed during the backtest."

print("\n" + "=" * 50)
print("PERFORMANCE SUMMARY")
print("=" * 50)
print(summary)

print("\n" + "=" * 50)
print("TRADE STATISTICS")
print("=" * 50)
print(stats)

# ----------------------------------
# MONTHLY RETURNS
# ----------------------------------
monthly_returns = (
    master_portfolio["portfolio_return"]
    .resample("ME")
    .apply(lambda x: (1 + x).prod() - 1)
)

# UPDATED PATH: Saved inside the data/ directory
monthly_returns.to_csv("data/monthly_returns.csv")


# ----------------------------------
# PLOT
# ----------------------------------
plt.figure(figsize=(12, 6))
plt.plot(
    master_portfolio.index,
    master_portfolio["equity_curve"],
    color='#1f77b4',
    linewidth=1.5
)
plt.title("Statistical Arbitrage: Sector-Neutral Pairs Trading (Gatev '06 Baseline)", fontsize=14)
plt.xlabel("Date", fontsize=12)
plt.ylabel("Cumulative Portfolio Value", fontsize=12)
plt.grid(True, alpha=0.3)
plt.axhline(1.0, color='black', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig("plots/equity_curve.png", dpi=300, bbox_inches='tight')
plt.show()