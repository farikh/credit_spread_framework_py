import pandas as pd

def calculate_rsi(prices, period=14):
    """
    Calculate the Relative Strength Index (RSI) for a given list of prices.

    :param prices: List of prices.
    :param period: The number of periods to use for the RSI calculation.
    :return: List of RSI values.
    """
    if len(prices) < period:
        raise ValueError("Not enough data points to calculate RSI.")

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gain = [delta if delta > 0 else 0 for delta in deltas]
    loss = [-delta if delta < 0 else 0 for delta in deltas]

    avg_gain = sum(gain[:period]) / period
    avg_loss = sum(loss[:period]) / period

    rsi_values = []
    for i in range(period, len(prices)):
        gain = (avg_gain * (period - 1) + (deltas[i - 1] if deltas[i - 1] > 0 else 0)) / period
        loss = (avg_loss * (period - 1) + (-deltas[i - 1] if deltas[i - 1] < 0 else 0)) / period

        rs = gain / loss if loss != 0 else float('inf')
        rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)

        avg_gain = gain
        avg_loss = loss

    return rsi_values

def calculate_bollinger_bands(prices, window=20, num_std_dev=2):
    """
    Calculate Bollinger Bands for a given list of prices.

    :param prices: List or pandas Series of prices.
    :param window: The number of periods for the moving average.
    :param num_std_dev: The number of standard deviations for the bands.
    :return: A tuple of (middle_band, upper_band, lower_band).
    """
    if isinstance(prices, list):
        prices = pd.Series(prices)

    middle_band = prices.rolling(window=window).mean()
    std_dev = prices.rolling(window=window).std()
    upper_band = middle_band + (num_std_dev * std_dev)
    lower_band = middle_band - (num_std_dev * std_dev)

    return middle_band, upper_band, lower_band