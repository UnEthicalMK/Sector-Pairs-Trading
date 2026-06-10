# Statistical Arbitrage: Sector-Neutral Pairs Trading Engine

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Type: Backtesting Engine](https://img.shields.io/badge/Domain-Quantitative_Research-purple.svg)

## Overview
This repository implements a robust, event-driven backtesting engine for equity statistical arbitrage. The core logic replicates the foundational **Distance Method** for pairs trading proposed by Gatev et al. (2006), enhanced with modern risk-management constraints including dynamic sector-neutral pairing, continuous price path normalization, and explicit transaction friction modeling.

The primary objective of this project is to demonstrate rigorous quantitative engineering pipelines, specifically focusing on the elimination of lookahead bias, the management of survivorship bias, and the construction of scalable, vectorized state machines for trade execution.

## System Architecture & Engineering

The engine is highly modular, separating data ingestion, statistical selection, and portfolio execution into distinct domains:

* **`data_loader.py`**: Handles ingestion and strict temporal slicing to prevent in-sample/out-of-sample data bleeding.
* **`sector_map.py`**: A localized caching engine that dynamically buckets the S&P 500 universe by GICS sectors to enforce industry-neutral pair selection.
* **`rolling_windows.py`**: Implements a strict walk-forward methodology (252-day formation, 126-day trading) capturing metadata for seamless downstream performance auditing.
* **`pair_selection.py`**: Optimizes the $O(N^2)$ computational bottleneck of global pair combinations by utilizing pre-sorted sector clusters, utilizing Sum of Squared Differences (SSD) as the primary distance metric.
* **`signal_generation.py`**: A high-speed, vectorized state machine governing entry thresholds, mean-reversion exits, standard-deviation stop-losses, and maximum-holding timeouts.
* **`portfolio.py` & `trade_log.py`**: Explicitly models capital allocation across short/long legs, time-shifts signals to eliminate execution lookahead bias, and deducts basis-point friction per execution.

## Methodology Enhancements (Beyond Gatev '06)

While the baseline logic relies on Euclidean distance, this engine implements several critical upgrades necessary for modern market environments:

1. **Intra-Sector Constraints:** By strictly pairing assets within identical GICS sectors, the engine mathematically insulates the portfolio from macroeconomic regime shifts and spurious correlations (e.g., matching a bank with an energy firm during a global market crash).
2. **Execution Friction:** Every opened and closed pair deducts a strict 6 bps (0.06%) friction penalty to account for exchange commissions and estimated liquidity slippage.
3. **Continuous Normalization:** Replaces hard-anchoring with localized `base_price` division, ensuring that overnight gaps and earnings jumps are preserved rather than falsely smoothed.

*Note on Survivorship Bias: Due to the constraints of free-tier financial APIs, universe selection utilizes the current S&P 500 constituency. In a true production environment, this module would be swapped for CRSP/Compustat Point-in-Time data to eliminate survivorship bias.*

## Repository Structure

```text
pairs-trading-engine/
├── data/                       # Cached JSON universe & output CSV logs
├── src/                        # Core execution modules
│   ├── __init__.py
│   ├── data_loader.py          # yfinance ingestion & cleaning
│   ├── performance.py          # Sharpe, Max DD, CAGR calculators
│   ├── pair_selection.py       # Sector-constrained SSD calculation
│   ├── portfolio.py            # Leverage, friction, and PnL aggregation
│   ├── preprocessing.py        # Price path normalization
│   ├── rolling_windows.py      # Walk-forward generator
│   ├── sector_map.py           # Cached Wikipedia GICS scraper
│   ├── signal_generation.py    # Core trade state machine
│   └── trade_log.py            # Geometric compounding extractor
├── main.py                     # Primary orchestration script
├── requirements.txt            
└── README.md