import numpy as np
import pandas as pd

def total_return(equity_curve):
    """
    Total cumulative return, agnostic to starting capital.
    """
    return (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1


def annualized_return(equity_curve, trading_days=252):
    """
    CAGR, protected against negative equity values.
    """
    n_years = len(equity_curve) / trading_days
    cumulative_return = equity_curve.iloc[-1] / equity_curve.iloc[0]
    
    # Mathematical protection: Cannot take a fractional root of a negative number
    if cumulative_return <= 0:
        return -1.0
        
    return (cumulative_return ** (1 / n_years)) - 1


def annualized_volatility(returns, trading_days=252):
    """
    Annualized volatility.
    """
    return returns.std() * np.sqrt(trading_days)


def sharpe_ratio(returns, risk_free_rate=0, trading_days=252):
    """
    Annualized Sharpe Ratio.
    """
    excess_returns = returns - (risk_free_rate / trading_days)
    volatility = excess_returns.std()

    # Prevent division by zero or infinitesimally small volatility
    if volatility <= 1e-9:
        return np.nan

    return (excess_returns.mean() / volatility) * np.sqrt(trading_days)


def max_drawdown(equity_curve):
    """
    Maximum drawdown.
    """
    running_max = equity_curve.cummax()
    drawdown = (equity_curve / running_max) - 1
    return drawdown.min()


def win_rate(returns):
    """
    Percentage of positive-return days (Note: This is Daily Win Rate, not Trade Win Rate).
    """
    active_returns = returns[returns != 0]

    if len(active_returns) == 0:
        return np.nan

    return (active_returns > 0).mean()


def summarize_performance(backtest_results):
    """
    Generate a summary table.
    """
    returns = backtest_results["net_return"]
    equity_curve = backtest_results["equity_curve"]

    summary = pd.Series(
        {
            "Total Return": total_return(equity_curve),
            "Annualized Return": annualized_return(equity_curve),
            "Annualized Volatility": annualized_volatility(returns),
            "Sharpe Ratio": sharpe_ratio(returns),
            "Max Drawdown": max_drawdown(equity_curve),
            "Daily Win Rate": win_rate(returns) # Explicitly renamed for clarity
        }
    )

    return summary