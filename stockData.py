
from enum import Enum
import os

import talib
import talib.abstract as ta
from talib import MA_Type
import dataframe

import pandas as pd 
import numpy as np

import util

class BuyState (Enum):
    STAY = 0
    BUY = 1
    SELL = 2

class StockData:
    def __init__(self, code, name, df):
        self.code_ = code
        self.name_ = name
        self.chartData_ = df
        
        self.buyCount_ = 0
        self.buyPrice_ = 0
        self.position_ = BuyState.STAY
        self.predicPrice_ = 0        # 머신러닝으로 예측한 다음날 주식값
        self.strategyAction_ = BuyState.STAY
        self.teleLog_ = ""
        self.marketCapRanking_ = 0

    def canPredic(self):
        size = len(self.chartData_)
        if size < 300:
            return False
        return True

    def calcPredicRate(self):
        if self.canPredic() == False:
            return 0
        
        nowPrice = self.candle0()
        rate = util.calcRate(nowPrice["close"], self.predicPrice_)
        return rate

    # 최신 캔들
    def candle0(self):
        rowCnt = self.chartData_.shape[0]
        if rowCnt == 0:
            return None
        return self.chartData_.iloc[-1]

    # 전날 캔들
    def candle1(self):
        rowCnt = self.chartData_.shape[0]
        if rowCnt <= 1:
            return None
        return self.chartData_.iloc[-2]

    # 
    def candle2(self):
        rowCnt = self.chartData_.shape[0]
        if rowCnt <= 2:
            return None
        return self.chartData_.iloc[-3]

    def calcProfit(self):
        if self.buyCount_ == 0:
            return 0
     
        profit = self.buyCount_ * self.buyPrice_
        return profit    

    # 각종 보조지표, 기술지표 계산
    def calcIndicator(self):        
        arrClose = np.asarray(self.chartData_["close"], dtype='f8')
        arrHigh = np.asarray(self.chartData_["high"], dtype='f8')
        arrLow = np.asarray(self.chartData_["low"], dtype='f8')
     
        # 이평선 계산
        self.chartData_["sma5"] = ta._ta_lib.SMA(arrClose, 5)
        self.chartData_["sma10"] = ta._ta_lib.SMA(arrClose, 10)
        self.chartData_["sma20"] = ta._ta_lib.SMA(arrClose, 20)
        self.chartData_["sma50"] = ta._ta_lib.SMA(arrClose, 50)
        self.chartData_["sma100"] = ta._ta_lib.SMA(arrClose, 100)
        self.chartData_["sma200"] = ta._ta_lib.SMA(arrClose, 200)

        self.chartData_["ema5"] = ta._ta_lib.EMA(arrClose, 5)
        self.chartData_["ema10"] = ta._ta_lib.EMA(arrClose, 10)
        self.chartData_["ema20"] = ta._ta_lib.EMA(arrClose, 20)
        self.chartData_["ema50"] = ta._ta_lib.EMA(arrClose, 50)
        self.chartData_["ema100"] = ta._ta_lib.EMA(arrClose, 100)
        self.chartData_["ema200"] = ta._ta_lib.EMA(arrClose, 200)

        self.chartData_["wma5"] = ta._ta_lib.WMA(arrClose, 5)
        self.chartData_["wma10"] = ta._ta_lib.WMA(arrClose, 10)
        self.chartData_["wma20"] = ta._ta_lib.WMA(arrClose, 20)
        self.chartData_["wma50"] = ta._ta_lib.WMA(arrClose, 50)
        self.chartData_["wma100"] = ta._ta_lib.WMA(arrClose, 100)
        self.chartData_["wma200"] = ta._ta_lib.WMA(arrClose, 200)

        macd, signal, osi = ta._ta_lib.MACD(arrClose, fastperiod=12, slowperiod=26, signalperiod=9)
        self.chartData_["MACD"] = macd
        self.chartData_["MACDSignal"] = signal
        self.chartData_["MACDOsi"] = osi
  
        #볼린저 계산
        upper, middle, low = ta._ta_lib.BBANDS(arrClose, 20, 2, 2, matype=MA_Type.SMA)
        self.chartData_["bbandUp"] = upper
        self.chartData_["bbandMid"] = middle
        self.chartData_["bbandLow"] = low

        # 기타 자주 사용되는 것들
        self.chartData_["rsi"] = ta._ta_lib.RSI(arrClose, 14)
        self.chartData_["cci"] = ta._ta_lib.CCI(arrHigh, arrLow, arrClose, 14)
        self.chartData_["williumR"] = ta._ta_lib.WILLR(arrHigh, arrLow, arrClose, 14)
        self.chartData_["parabol"] = ta._ta_lib.VAR(arrClose, 5, 1)
        self.chartData_["adx"]  = ta._ta_lib.ADX(arrHigh, arrLow, arrClose, 14)
        self.chartData_["plusDI"]  = ta._ta_lib.PLUS_DI(arrHigh, arrLow, arrClose, 14)
        self.chartData_["plusDM"]  = ta._ta_lib.PLUS_DM(arrHigh, arrLow, 14)
       
        self.chartData_["atr"] = ta._ta_lib.ATR(arrHigh, arrLow, arrClose, 30)
        