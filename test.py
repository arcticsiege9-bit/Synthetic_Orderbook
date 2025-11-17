import pandas as pd
import numpy as np 
from pandas import *
from backtesting import *
from backtesting.lib import *
from backtesting.test import *
from orderbook import df

def convert_df():
    data = pd.DataFrame({
        # OHLC
        'Open': df['mid'].shift(1),
        'High': df['ask'],
        'Low': df['bid'],
        'Close': df['mid'],
        'Volume': df['volume']
    })

    data = data.drop(index=0)
    data.index = df['datetime'].drop(index=0)

    return data

df = convert_df()

class strategy_ins(Strategy):

    # Define the two MA lags as *class variables*
    # for later optimization
    n1 = 7
    n2 = 22

    def init(self):
        # Precompute the two moving averages
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)
    
    def next(self):
        # If sma1 crosses above sma2, close any existing
        # short trades, and buy the asset
        if crossover(self.sma1, self.sma2):
            self.position.close()
            self.buy()

        # Else, if sma1 crosses below sma2, close any existing
        # long trades, and sell the asset
        elif crossover(self.sma2, self.sma1):
            self.position.close()
            self.sell()



bt = Backtest(df, strategy_ins,
              cash=50000,
              exclusive_orders=True)

bt.run()
bt.plot(filename='graph', plot_trades=False, resample=True, plot_volume=False, open_browser=True)