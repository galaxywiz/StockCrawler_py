import numpy as np
from stockData import StockData, BuyState

#//---------------------------------------------------//
class TradeStrategy:
    def setStockData(self, stockData):
        self.stockData_ = stockData

    def buy(self, timeIdx):
        pass

    def sell(self, timeIdx):
        pass

    def buyList(self):
        pass

    def sellList(self):
        pass

#//---------------------------------------------------//
class MaTradeStrategy(TradeStrategy):  
    def __init__(self, fast = "ema5", slow = "ema20"):
        self.MA_FAST = fast
        self.MA_SLOW = slow

    def __crossUp(self, timeIdx):
        if timeIdx < 1:
            return False

        chartData = self.stockData_.chartData_
        prevCandle = chartData.iloc[timeIdx - 1]
        fast = prevCandle[self.MA_FAST]
        slow = prevCandle[self.MA_SLOW]
        if fast < slow:
            nowCandle = chartData.iloc[timeIdx]
            fast = nowCandle[self.MA_FAST]
            slow = nowCandle[self.MA_SLOW]

            if fast > slow:
                return True

        return False

    def __crossDown(self, timeIdx):
        if timeIdx < 1:
            return False
            
        chartData = self.stockData_.chartData_
        prevCandle = chartData.iloc[timeIdx - 1]
        fast = prevCandle[self.MA_FAST]
        slow = prevCandle[self.MA_SLOW]
        if fast > slow:
            nowCandle = chartData.iloc[timeIdx]
            fast = nowCandle[self.MA_FAST]
            slow = nowCandle[self.MA_SLOW]

            if fast < slow:
                return True

        return False

    def buy(self, timeIdx):
        if self.stockData_.position_ == BuyState.STAY:
            if self.__crossUp(timeIdx):
                return True
        return False

    def sell(self, timeIdx):
        if self.stockData_.position_ == BuyState.STAY:
            if self.__crossDown(timeIdx):
                return True
        return False

    def buyList(self):
        signalList = []
        signalList.append(np.nan)
        chartData = self.stockData_.chartData_

        for i in range(1, len(chartData)):
            nowCandle = chartData.iloc[i]
            if self.__crossUp(i):
                signalList.append(nowCandle["close"])
            else:
                signalList.append(np.nan)

        return signalList

    def sellList(self):
        signalList = []
        signalList.append(np.nan)
        chartData = self.stockData_.chartData_

        for i in range(1, len(chartData)):
            nowCandle = chartData.iloc[i]
            if self.__crossDown(i):
                signalList.append(nowCandle["close"])
            else:
                signalList.append(np.nan)

        return signalList       

#//---------------------------------------------------//
class MACDTradeStrategy(TradeStrategy):
    TERM = 1
    def __buySignal(self, timeIdx):
        if timeIdx < self.TERM:
            return False
            
        chartData = self.stockData_.chartData_
        prevCandle = chartData.iloc[timeIdx - 1]
        macd = prevCandle["MACD"]
        signal = prevCandle["MACDSignal"]
        if macd > signal:
            nowCandle = chartData.iloc[timeIdx]
            macd = nowCandle["MACD"]
            signal = nowCandle["MACDSignal"]

            if macd < signal:
                return True

        return False

    def __sellSignal(self, timeIdx):
        if timeIdx < 1:
            return False
            
        chartData = self.stockData_.chartData_
        prevCandle = chartData.iloc[timeIdx - 1]
        macd = prevCandle["MACD"]
        signal = prevCandle["MACDSignal"]
        if macd < signal:
            nowCandle = chartData.iloc[timeIdx]
            macd = nowCandle["MACD"]
            signal = nowCandle["MACDSignal"]

            if macd > signal:
                return True

        return False

    def buy(self, timeIdx):
        chartData = self.stockData_.chartData_
        if len(chartData) <= self.TERM:
            return False

        if self.stockData_.position_ == BuyState.STAY:
            if self.__buySignal(timeIdx):
                return True
        return False

    def sell(self, timeIdx):
        chartData = self.stockData_.chartData_
        if len(chartData) <= self.TERM:
            return False

        if self.stockData_.position_ == BuyState.STAY:
            if self.__sellSignal(timeIdx):
                return True
        return False

    def buyList(self):
        signalList = []
        for i in range(0, self.TERM):
            signalList.append(np.nan)
        
        chartData = self.stockData_.chartData_

        for i in range(self.TERM, len(chartData)):
            nowCandle = chartData.iloc[i]
            if self.__buySignal(i):
                signalList.append(nowCandle["close"])
            else:
                signalList.append(np.nan)

        return signalList

    def sellList(self):
        signalList = []
        for i in range(0, self.TERM):
            signalList.append(np.nan)
        
        chartData = self.stockData_.chartData_

        for i in range(self.TERM, len(chartData)):
            nowCandle = chartData.iloc[i]
            if self.__sellSignal(i):
                signalList.append(nowCandle["close"])
            else:
                signalList.append(np.nan)

        return signalList
        
#//---------------------------------------------------//
class LarryRTradeStrategy(TradeStrategy):
    RANGE = 20

    def noice(self, timeIdx):
        return 0.7

    def __buySignal(self, timeIdx):
        chartData = self.stockData_.chartData_
        noice = self.noice(timeIdx)
        candle = chartData.iloc[timeIdx]
        startPrice = candle["start"]
        closePrice = candle["close"]
        stand = startPrice + ((candle["high"] - candle["low"]) * noice)

        if closePrice > stand:
            return True
        return False

    def __sellSignal(self, timeIdx):
        chartData = self.stockData_.chartData_
        noice = self.noice(timeIdx)
        candle = chartData.iloc[timeIdx]
        startPrice = candle["start"]
        closePrice = candle["close"]
        stand = startPrice - ((candle["high"] - candle["low"]) * noice)

        if closePrice < stand:
            return True
        return False

    def buy(self, timeIdx):
        chartData = self.stockData_.chartData_
        if len(chartData) <= self.RANGE:
            return False

        if self.stockData_.position_ == BuyState.STAY:
            if self.__buySignal(timeIdx):
                return True
        return False

    def sell(self, timeIdx):
        chartData = self.stockData_.chartData_
        if len(chartData) <= self.RANGE:
            return False

        if self.stockData_.position_ == BuyState.STAY:
            if self.__sellSignal(timeIdx):
                return True
        return False

    def buyList(self):
        signalList = []
        for i in range(0, self.RANGE):
            signalList.append(np.nan)
        
        chartData = self.stockData_.chartData_

        for i in range(self.RANGE, len(chartData)):
            nowCandle = chartData.iloc[i]
            if self.__buySignal(i):
                signalList.append(nowCandle["close"])
            else:
                signalList.append(np.nan)

        return signalList

    def sellList(self):
        signalList = []
        for i in range(0, self.RANGE):
            signalList.append(np.nan)
        
        chartData = self.stockData_.chartData_

        flag = False
        for i in range(self.RANGE, len(chartData)):
            nowCandle = chartData.iloc[i]
            if flag:
                signalList.append(nowCandle["close"])
                flag = False
                continue

            if self.__buySignal(i):
                flag = True
            
            signalList.append(np.nan)

        return signalList    