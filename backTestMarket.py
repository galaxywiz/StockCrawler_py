import pandas as pd 
from pandas import Series, DataFrame
import numpy as np
import dataframe
from datetime import datetime, timedelta

import botConfig
from agent import Agent
from stockCrawler import USAStockCrawler, KoreaStockCrawler
from sqliteStockDB import DayPriceDB, DayPriceFloatDB
from stockData import StockData, BuyState
from telegram import TelegramBot
from stockPredic import StockPredic

from tradeStrategy import MaTradeStrategy, LarryRTradeStrategy, MACDTradeStrategy

class BackTestMarket:
    def __init__(self, botConfig):
        self.stockPool_ = {}
        self.config_ = botConfig

    #-------------------------------------------------#
    def __loadFromDB(self, code):
        st = self.startTime_
        ret, df = self.config_.dayPriceDB_.load(code, startTime = st)
        if ret == False:
            return False, None

        for index, candle in df.iterrows():
            ct = candle["candleTime"]
            if ct == st:
                return ret, df
        
        return False, None
        
     ## db 에서 데이터 봐서 있으면 말고 없으면 로딩
    def __loadStockData(self, name, code):  
        ret, df = self.__loadFromDB(code)
        if ret == False:
            print("*%s, %s load 실패" % (name, code))
            return None

        sd = StockData(code, name, df)
        self.stockPool_[name] = sd
        sd.calcIndicator()
        print("*%s, %s load 완료" % (name, code))

    def __getStocksList(self):
        self.stockPool_.clear()
        isFileLoad = self.config_.isFileLoad_
        if isFileLoad:
            fileName = self.config_.listFileName_
            stockDf = self.config_.crawler_.getStocksListFromFile(fileName)
        else: 
            tableLimit = -1
            isDebug = True
            stockDf = self.config_.crawler_.getStocksList(tableLimit, debug=isDebug)    # 웹에 있는 2300여개 종목을 긁어온다.

        # 주식의 일자데이터 크롤링 / db 에서 갖고 오기
        for idxi, rowCode in stockDf.iterrows():
            name = rowCode['name']
            code = rowCode['code']
            self.__loadStockData(name, code)
        print("[%d] 개 로딩 완료" % len(self.stockPool_))

    # 일봉을 기준으로 주식 데이터를 하나 하나 추가해 주는 클래스
    def __setTimeMatrix(self, startTime, endTime):
        marketTime = startTime

        print("* make time table [%04d/%02d/%02d] process" % (marketTime.year, marketTime.month, marketTime.day))
        delList = []
        for code, sd in self.stockPool_.items():
            index, candle = sd.getCandle(marketTime.strftime(self.DATE_FMT))
            if index < 0:
                delList.append(code)
                continue

            sd.backTestIter_ = index

        for code in delList:
            sd = self.stockPool_[code]
            print("[%s] backckTest remove" % sd.name_)
            del self.stockPool_[code]

        print("타임 테이블 생성 완료")
    #-------------------------------------------------#
    DATE_FMT = "%Y-%m-%d"
    
    def __doTest(self, sd, forRange, strategy):
        agent = Agent(1000*1000)
        strategy.setStockData(sd)

        print("* [%s] 의 백테스트 [%d] 투자, 전략 [%s]" % (sd.name_, agent.account_, strategy.__class__.__name__))

        for timeIdx in forRange:
            # 보유 주식 매도 신호?
            if agent.haveStock(sd.code_):
                if strategy.sell(timeIdx):
                    agent.payOff(sd.code_, timeIdx)
                    continue

            # 주식 매수 신호?
            if strategy.buy(timeIdx):
                agent.buy(sd, timeIdx)
                continue
        
        initAccount = agent.initAccount_
        finalAsset = agent.calcAsset() 
        strategtName = strategy.__class__.__name__
        if initAccount < finalAsset:
            winCnt = self.winStatic_[strategtName] + 1
            self.winStatic_[strategtName] = winCnt

        value = self.accountStatic_[strategtName] + finalAsset
        self.accountStatic_[strategtName] = value
        print("Agent [%d] 금액 -> [%d] 로 변화" % (initAccount, finalAsset))

    def processMarket(self, startTime, endTime):
        self.startTime_ = startTime.strftime(self.DATE_FMT)
        print("백테스트 기간 [%04d/%02d/%02d] -> [%04d/%02d/%02d]" % (startTime.year, startTime.month, startTime.day, endTime.year, endTime.month, endTime.day))
        self.__getStocksList()
        self.__setTimeMatrix(startTime, endTime)

        strategyList = [LarryRTradeStrategy(), MaTradeStrategy(), MACDTradeStrategy()]
        self.winStatic_ = {}
        self.winStatic_[LarryRTradeStrategy().__class__.__name__] = 0
        self.winStatic_[MaTradeStrategy().__class__.__name__] = 0
        self.winStatic_[MACDTradeStrategy().__class__.__name__] = 0

        self.accountStatic_ = {}
        self.accountStatic_[LarryRTradeStrategy().__class__.__name__] = 0
        self.accountStatic_[MaTradeStrategy().__class__.__name__] = 0
        self.accountStatic_[MACDTradeStrategy().__class__.__name__] = 0

        for code, sd in self.stockPool_.items():
            index = sd.backTestIter_ + 100
            totalLen = len(sd.chartData_)
            if index > totalLen:
                continue
            
            for strategy in strategyList:
                self.__doTest(sd, range(index, totalLen), strategy)

        totalCnt = len(self.stockPool_)
        print("전체 체크해본 주식 갯수[%d]" % totalCnt)
        for strategyName, winCnt in self.winStatic_.items():
            print("* [%s]전략 [%d]/[%d] 번 승리함." % (strategyName, winCnt, totalCnt))
            print("-> [%s]전략 총 [%d] 이익금 / 건당 평균 [%f]" % (strategyName, self.accountStatic_[strategyName], self.accountStatic_[strategyName]/totalCnt))