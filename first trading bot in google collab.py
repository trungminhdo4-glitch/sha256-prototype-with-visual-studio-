pip install yfinance import numpy as np

import pandas as pd

import yfinance as yf

import warnings

warnings.filterwarnings("ignore") # The code here will allow you to switch your graphics to dark mode for those who choose to code in dark mode

import matplotlib.pyplot as plt



import matplotlib as mpl

from matplotlib import cycler

colors = cycler('color',

                ['#669FEE', '#66EE91', '#9988DD',

                 '#EECC55', '#88BB44', '#FFBBBB'])

plt.rc('figure', facecolor='#313233')

plt.rc('axes', facecolor="#313233", edgecolor='none',

       axisbelow=True, grid=True, prop_cycle=colors,

       labelcolor='gray')

plt.rc('grid', color='474A4A', linestyle='solid')

plt.rc('xtick', color='gray')

plt.rc('ytick', direction='out', color='gray')

plt.rc('legend', facecolor="#313233", edgecolor="#313233")

plt.rc("text", color="#C9C9C9") import datetime



def preprocessing_yf(symbol):

  # Get current date

  end_date = datetime.date.today()

  # Get start date (e.g., 5 years ago)

  start_date = end_date - datetime.timedelta(days=5*365) # Approximately 5 years



  #Import the data for a longer period

  df = yf.download(symbol, start=start_date, end=end_date).dropna()



  #Rename - Adjusted for 5 columns as 'Adj Close' is often not present for currency pairs

  df.columns = ["open", "high", "low", "close", "volume"]

  df.index.name = "time"



  # 'adj close' column is usually not present for currency data, so no need to delete it.

  # del df["adj close"]



  return df



df = preprocessing_yf("EURUSD=X")

df # Create Simple moving average 30 days

df["SMA fast"] = df["close"].rolling(30).mean()



# Create Simple moving average 60 days

df["SMA slow"] = df["close"].rolling(60).mean()



# Plot the results

df[["close", "SMA fast", "SMA slow"]].loc["2025"].plot(figsize=(15,8)) # Create an empty columns to put the signals

df["signal"]=np.nan



# Create the condition

condition_buy = (df["SMA fast"] > df["SMA slow"]) & (df["SMA fast"].shift(1) < df["SMA slow"].shift(1))

condition_sell = (df["SMA fast"] < df["SMA slow"]) & (df["SMA fast"].shift(1) > df["SMA slow"].shift(1))



df.loc[condition_buy, "signal"] = 1

df.loc[condition_sell, "signal"] = -1 # We plot all the signla to be sure that they be correct



year="2025"



# Select all signal in a index list to plot only this points

idx_open = df.loc[df["signal"] == 1].loc[year].index

idx_close = df.loc[df["signal"] == -1].loc[year].index







# Adapt the size of the graph

plt.figure(figsize=(30,12))



# Plot the points of the open long signal in green and sell in red

plt.scatter(idx_open, df.loc[idx_open]["close"].loc[year], color= "#57CE95", marker="^")

plt.scatter(idx_close, df.loc[idx_close]["close"].loc[year], color= "red", marker="v")





# Plot the resistance to be sure that the conditions are completed

plt.plot(df["close"].loc[year].index, df["close"].loc[year], alpha=0.35)



plt.plot(df["close"].loc[year].index, df["SMA fast"].loc[year], alpha=0.35)



plt.plot(df["close"].loc[year].index, df["SMA slow"].loc[year], alpha=0.35)



plt.legend(["Buy", "Sell", "EURUSD"])



# Show the graph

plt.show() # We say signal when we open or close a trade and poistion to talk about the whole time we are into a trade

df["position"] = df["signal"].fillna(method="ffill")



# We define a fix cost we need to pay each time we interact with the market

cost_ind = 0.0001



# We create a vector of cost

df["cost"] = (np.abs(df["signal"]) * cost_ind).fillna(value=0) #(-0.0001, 0, 0, 0, 0, 0 , 0, -0.0001, 0, 0) (-0.0001,-0.0001,-0.0001,-0.0001,-0.0001,)



# Compute the percentage of variation of the asset

df["pct"] = df["close"].pct_change(1)



# Compute the return of the strategy

df["return"] = (df["pct"] * df["position"].shift(1) - df["cost"])*100





df["return"].cumsum().plot(figsize=(30,12), title="Return for the Trend trading stratgey on the EURUSD")

plt.show() def SMA_strategy(input, fast_sma=30, slow_sma=60, cost_ind=0.0001):



  df = preprocessing_yf(input)





  # Create Resistance using a rolling max

  df["SMA fast"] = df["close"].rolling(fast_sma).mean()



  # Create Support using a rolling min

  df["SMA slow"] = df["close"].rolling(slow_sma).mean()



  # Create an empty columns to put the signals

  df["signal"]=np.nan



  # Create the condition

  condition_buy = (df["SMA fast"] > df["SMA slow"]) & (df["SMA fast"].shift(1) < df["SMA slow"].shift(1))

  condition_sell = (df["SMA fast"] < df["SMA slow"]) & (df["SMA fast"].shift(1) > df["SMA slow"].shift(1))



  df.loc[condition_buy, "signal"] = 1

  df.loc[condition_sell, "signal"] = -1



  # We say signal when we open or close a trade and poistion to talk about the whole time we are into a trade

  df["position"] = df["signal"].fillna(method="ffill")



  # We create a vector of cost

  df["cost"] = (np.abs(df["signal"]) * cost_ind).fillna(value=0)



  # Compute the percentage of variation of the asset

  df["pct"] = df["close"].pct_change(1)



  # Compute the return of the strategy

  df["return"] = (df["pct"] * df["position"].shift(1) - df["cost"])*100





  return df["return"] SMA_strategy("BTC-USD", 30,60,0.001).cumsum().plot(figsize=(30,12), title="Return for the Trend trading stratgey", ylabel="P&L in %")

plt.show()
