# 주식 데이터 수집해서 매매 신호 찾고 처리하는
# 주식 봇을 기술
from enum import Enum
import pandas as pd 
from pandas import Series, DataFrame
import numpy as np
import dataframe
from datetime import datetime
from datetime import timedelta
import time
import os
import shutil
import glob
import locale
import util

import botConfig
from stockCrawler import USAStockCrawler, KoreaStockCrawler
from sqliteStockDB import DayPriceDB, DayPriceFloatDB
from stockData import StockData, BuyState
from telegram import TelegramBot
from stockPredic import StockPredic
from printChart import PrintChart
from telegram import TelegramBot
from tradeStrategy import MaTradeStrategy, LarryRTradeStrategy, MACDTradeStrategy

class Bot:
    REFRESH_DAY = 1

    def __init__(self, botConfig):
        self.stockPool_ = {}
        self.config_ = botConfig
        self.telegram_ = TelegramBot(token = botConfig.telegramToken_, id = botConfig.telegramId_)

        locale.setlocale(locale.LC_ALL, '')
        now = datetime.now() - timedelta(days=1)  
        self.lastCrawlingTime_ = now

    def __process(self):
        self.getStocksList()
        self.checkStrategy()
        
        now = time.localtime()
        current = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        print("[%s] 갱신 완료" % current)

    def __doScheduler(self):
        now = datetime.now()
        print("[%s] run" % self.config_.__class__.__name__)

        if self.config_.crawlingTime():
            elpe = now - self.lastCrawlingTime_
            if elpe.total_seconds() < (60*60*24 - 600):
                return
            
            self.lastCrawlingTime_ = datetime.now()
            self.__process()

    #----------------------------------------------------------#
    def sendMessage(self, log):
        TelegramBot.sendMessage(self, log)
  
    #----------------------------------------------------------#
    # db 에 데이터 저장 하고 로딩!
    def __getStockInfoFromWeb2DB(self, name, code):
        loadDays = 10
        # DB에 데이터가 없으면 테이블을 만듬
        sel = self.config_.dayPriceDB_.getTable(code)
        if sel == 0:
            return None
        elif sel == 1:  # 신규 생성 했으면
            loadDays = 365*5  #5 년치

        # 크롤러에게 code 넘기고 넷 데이터 긁어오기
        df = self.config_.crawler_.getStockData(code, loadDays)
        if df is None:
            print("! 주식 [%s] 의 크롤링 실패" % (name))
            return None

        # 데이터 저장      
        self.config_.dayPriceDB_.save(code, df)
        print("====== 주식 일봉 데이터 [%s] 저장 완료 =====" % (name))

    def __loadFromDB(self, code):
        ret, df = self.config_.dayPriceDB_.load(code)
        if ret == False:
            return False, None

        return True, df

    ## db 에서 데이터 봐서 있으면 말고 없으면 로딩
    def __loadStockData(self, name, code, marketCapRanking):  
        now = datetime.now()
        ret, df = self.__loadFromDB(code)
            
        if ret == False:
            self.__getStockInfoFromWeb2DB(name, code)
            ret, df = self.__loadFromDB(code)
            if ret == False:
                return None
        else:
            dateStr = df.iloc[-1]['candleTime']
            candleDate = datetime.strptime(dateStr, "%Y-%m-%d")
            elpe = (now - candleDate).days
            if elpe > self.REFRESH_DAY:
                self.__getStockInfoFromWeb2DB(name, code)
                ret, df = self.__loadFromDB(code)
                if ret == False:
                    return None

        #30일전 데이터가 있는지 체크
        if len(df) < 35:
            return None

        prevDateStr = df.iloc[-15]['candleTime']
        candleDate = datetime.strptime(prevDateStr, "%Y-%m-%d")
        elpe = (now - candleDate).days
        if elpe > 30:
            print("%s 데이터 로딩 실패" % name)
            return None

        sd = StockData(code, name, df)
        self.stockPool_[name] = sd
        sd.calcIndicator()
        sd.marketCapRanking_ = marketCapRanking

        print("*%s, %s load 완료" % (name, code))

    def getStocksList(self, limit = -1):
        self.stockPool_.clear()
        isFileLoad = self.config_.isFileLoad_
        if isFileLoad:
            fileName = self.config_.listFileName_
            stockDf = self.config_.crawler_.getStocksListFromFile(fileName)
        else: 
            tableLimit = self.config_.limitSize_
            stockDf = self.config_.crawler_.getStocksList(tableLimit)    # 웹에 있는 종목을 긁어온다.
            
        # 주식의 일자데이터 크롤링 / db 에서 갖고 오기
        for idxi, rowCode in stockDf.iterrows():
            name = rowCode['name']
            code = rowCode['code']
            marketCapRanking = rowCode['ranking']
            if type(name) != str:
                continue
            self.__loadStockData(name, code, marketCapRanking)
            if limit > 0:
                if idxi > limit:
                    break
    #----------------------------------------------------------#
    def __checkNowTime(self, sd):
        now = datetime.now()
        nowCandle = sd.candle0()
        dateStr = nowCandle["candleTime"]
        candleDate = datetime.strptime(dateStr, "%Y-%m-%d")
        elpe = (now - candleDate).days
        
        temp = self.REFRESH_DAY
        if now.weekday() == 6:
            temp += 2

        if elpe <= temp:
            return True
        return False

    def __doPredic(self, sd):
        vm = StockPredic(sd)
        predicPrice = vm.predic()
        sd.predicPrice_ = predicPrice[0]
        del vm

    def __drawChart(self, sd):
        # 시그널 차트화를 위한 
        chartMaker = PrintChart() 
        dir = self.config_.chartDir_
        chartPath = chartMaker.saveFigure(dir, sd)
        del chartMaker

        return chartPath

    def checkStrategy(self):
        now = datetime.now()
        time = now.strftime("%Y-%m-%d")
                
        for name, sd in self.stockPool_.items():
            if self.__checkNowTime(sd) == False:
                continue

            nowCandle = sd.candle0()
            nowPrice = nowCandle["close"]

            strategy = self.config_.strategy_
            strategy.setStockData(sd)
            action = BuyState.STAY
            timeIdx = len(sd.chartData_) - 1
            
            # 고전 전략 (EMA 골든 크로스로 판단)
            if strategy.buy(timeIdx):
                self.__doPredic(sd)
                action = BuyState.BUY
                sd.teleLog_ = "[%s][%s] 시총 순위[%d]\n" % (time, sd.name_, sd.marketCapRanking_)
                sd.teleLog_ +=" * [%s] long(매수) 신호\n" % (strategy.__class__.__name__)

            elif strategy.sell(timeIdx):
                self.__doPredic(sd)
                action = BuyState.SELL
                sd.teleLog_ = "[%s][%s] 시총 순위[%d]\n" % (time, sd.name_, sd.marketCapRanking_)
                sd.teleLog_ +=" * [%s] short(매도) 신호\n" % (strategy.__class__.__name__)
             
            sd.strategyAction_ = action

            if sd.strategyAction_ != BuyState.STAY:
                # if self.config_.isStock_:
                #     if sd.strategyAction_ == BuyState.BUY:
                #         if nowPrice > sd.predicPrice_:
                #             continue
                
                # sd.teleLog_ +=" * 금일 종가[%f] -> 예측[%f]\n" % (nowPrice, sd.predicPrice_)
                webSite = self.config_.baseWebSite_ % (sd.code_)
                sd.teleLog_ += webSite

                # 시그널 차트화를 위한 
                chartData = sd.chartData_
                chartData["BuySignal"] = strategy.buyList()
                chartData["SellSignal"] = strategy.sellList()
                chartPath = self.__drawChart(sd)
                if chartPath != None:
                    self.telegram_.sendPhoto(chartPath, sd.teleLog_) 

        self.config_.dayPreDB_.saveStockData(self.stockPool_)

    #----------------------------------------------------------#
    def do(self):
        self.__doScheduler()
