import dataframe
from datetime import datetime
from datetime import timedelta
import time
import util

from stockCrawler import USAStockCrawler, KoreaStockCrawler
from sqliteStockDB import DayPriceDB, DayPriceFloatDB
from stockData import StockData, BuyState
from tradeStrategy import MaTradeStrategy, LarryRTradeStrategy, MACDTradeStrategy

# 봇 설정
class BotConfig:
    def crawlingTime(self):
        pass

#---------------------------------------------------------#
class KoreaBotConfig(BotConfig):
    def __init__(self):
        self.telegramToken_ = "1080369141:AAFfXa9y70x-wqR2nJBKCVMNLmNFpm8kwA0"
        self.telegramId_ = "108036914" 
        
        self.isFileLoad_ = False
        #self.listFileName_ = "Kr_watchList.txt"
        self.crawler_ = KoreaStockCrawler()
        self.dayPriceDB_ = DayPriceDB("KoreaStockData.db", "day_price")
        self.chartDir_ = "chart_Korea/"
        self.baseWebSite_ = "http://finance.daum.net/quotes/A%s"
        self.strategy_ = MACDTradeStrategy()
        self.isStock_ = True
        self.limitSize_ = 250
        
    def crawlingTime(self):
        now = time.localtime()
        startHour = 16
        startMin = 30
        if now.tm_wday < 5:
            if now.tm_hour == startHour and now.tm_min >= startMin: 
                return True
        return False

#---------------------------------------------------------#
class USABotConfig(BotConfig):
    def __init__(self):
        self.telegramToken_ = "1080369141:AAFfXa9y70x-wqR2nJBKCVMNLmNFpm8kwA0"
        self.telegramId_ = "108036914" 

        self.isFileLoad_ = False
        #self.listFileName_ = "USA_watchList.txt"
        self.crawler_ = USAStockCrawler()
        self.dayPriceDB_ = DayPriceFloatDB("USAStockData.db","day_price")
        self.chartDir_ = "chart_USA/"
        self.baseWebSite_ = "https://finance.yahoo.com/quote/%s"
        self.strategy_ = MACDTradeStrategy()
        self.isStock_ = True
        self.limitSize_ = 200

    def crawlingTime(self):
        now = time.localtime()
        startHour = 7
        startMin = 0
        if 0 < now.tm_wday and now.tm_wday < 6:
            if now.tm_hour == startHour and now.tm_min >= startMin: 
                return True
        return False
