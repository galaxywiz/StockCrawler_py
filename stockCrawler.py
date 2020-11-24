# 인터넷에서 주식 데이터를 가지고 옵니다.
# 한국주식, 미국주식
#  
import pandas as pd 
from pandas import Series, DataFrame
from pandas_datareader import data as web
import numpy as np
import dataframe
import urllib.request
from bs4 import BeautifulSoup
import os
import time
import yfinance as yf
 
from datetime import datetime
from datetime import timedelta
 
#----------------------------------------------------------#
# 주식 목록 갖고오기 (상위)
class StockCrawler:
    def __getNaverURLCode(self, code):    
        url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=code)
        print("요청 URL = {}".format(url))
        return url

    # 종목 이름을 입력하면 종목에 해당하는 코드를 불러오기
    def __getNaverStockURL(self, item_name, stockDf):
        code = stockDf.query("name=='{}'".format(item_name))['code'].to_string(index=False)
        url = self.__getNaverURLCode(code)
        return url

    # 네이버에서 주식 데이터를 긁어 온다.
    def getKoreaStockDataFromNaver(self, ticker, loadDays):
        # 일자 데이터를 담을 df라는 DataFrame 정의
        df = pd.DataFrame()
        try:
            url = self.__getNaverURLCode(ticker)
            loadDays = (loadDays / 10) + 1
            # 1페이지가 10일. 100페이지 = 1000일 데이터만 가져오기 
            for page in range(1, int(loadDays)):
                pageURL = '{url}&page={page}'.format(url=url, page=page)
                df = df.append(pd.read_html(pageURL, header=0)[0], ignore_index=True)
            
            # df.dropna()를 이용해 결측값 있는 행 제거 
            df = df.dropna()
            df.reset_index(inplace=True, drop=False)
            stockDf = pd.DataFrame(df, columns=['날짜', '시가', '고가', '저가', '종가', '거래량'])
            stockDf.rename(columns={'날짜': 'candleTime', '고가': 'high', '저가': 'low', '시가': 'start', '종가': 'close', '거래량' : 'vol'}, inplace = True)
            stockDf['candleTime'] = stockDf['candleTime'].str.replace(".", "-")
            
            print(stockDf)
            return stockDf
        except:
            return None

    #파일에서 로딩할떄 “종목:코드:순위” 형식으로 로딩
    def _loadFromFile(self, targetList):
        stockDf = DataFrame(columns = ("name", "code","ranking"))
        for text in targetList:
            tokens = text.split(':')
            row = DataFrame(data=[tokens], columns=["name", "code","ranking"])
            stockDf = stockDf.append(row)
            stockDf = stockDf.reset_index(drop=True)
        return stockDf
   
    #일부 종목만 지정해서 로딩하고 싶을 때
    def getStocksListFromFile(self, fileName):
        with open(fileName, "r", encoding="utf-8") as f:
            targetList = f.read().splitlines()
        return self._loadFromFile(targetList)
 
#----------------------------------------------------------#
### 아후에서 데이터 긁어오기.
class KoreaStockCrawler(StockCrawler):
    def __getTicker(self, ticker):
        # 코스피는 KS, 코스닥은 KQ
        t = ticker + ".KS"
        try:
            p = web.get_quote_yahoo(t)['marketCap']
            return t
        except:
            return ticker +".KQ"
 
    def getStockData(self, ticker, loadDays):
        rowTicker = ticker
 
        try:
            ticker = self.__getTicker(ticker)
            oldDate = datetime.now() - timedelta(days=loadDays)
            fromDate = oldDate.strftime("%Y-%m-%d")
            stockDf = web.DataReader(ticker, start = fromDate, data_source='yahoo')
            if len(stockDf) == 0:
                return self.getKoreaStockDataFromNaver(rowTicker, loadDays)
 
            stockDf.reset_index(inplace=True, drop=False)
            stockDf.rename(columns={'Date': 'candleTime', 'High': 'high', 'Low': 'low', 'Open': 'start', 'Close': 'close', 'Volume' : 'vol'}, inplace = True)
            stockDf['candleTime'] = stockDf['candleTime'].dt.strftime("%Y-%m-%d")
 
            stockDf = pd.DataFrame(stockDf, columns=['candleTime', 'start', 'high', 'low', 'close', 'vol'])
            print(stockDf)
            return stockDf
 
        except:
            return self.getKoreaStockDataFromNaver(rowTicker, loadDays)
   
    def getStocksList(self, limit, debug = False):
        # 한국 주식 회사 등록 정보 가지고 오기
        stockDf = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13', header=0)[0]
        stockDf.종목코드 = stockDf.종목코드.map('{:06d}'.format)
        stockDf = stockDf[['회사명', '종목코드']] 
        stockDf = stockDf.rename(columns={'회사명': 'name', '종목코드': 'code'})
        
        # 시총 구하기
        marketCapList = []
        ranking = []
        dropIdx = []
        for idx, row in stockDf.iterrows():
            try:
                if debug == False:
                    ticker = self.__getTicker(row['code'])
                    p = web.get_quote_yahoo(ticker)['marketCap']
                    marketCap = int(p.values[0])
                    marketCapList.append(marketCap)
                else:
                    marketCapList.append(idx)
            except:
                dropIdx.append(idx)
                print("[%s][%s] 시총 갖고오기 에러" % (row['name'], row['code']))
        
        stockDf.drop(dropIdx, inplace = True)
 
        rank = 1
        for i in marketCapList:
            ranking.append(rank)
            rank += 1
 
        stockDf['MarketCap'] = marketCapList
        stockDf = stockDf.sort_values(by='MarketCap', ascending=False)
        stockDf['ranking'] = ranking
        if limit > 0:
            stockDf = stockDf[:limit]
        return stockDf
 
# 미국 주식 긁어오기
class USAStockCrawler(StockCrawler):
    def getStockData(self, ticker, loadDays):
        oldDate = datetime.now() - timedelta(days=loadDays)
        fromDate = oldDate.strftime("%Y-%m-%d")
        try:
            stockDf = web.DataReader(ticker, start = fromDate, data_source='yahoo')
            
            stockDf.reset_index(inplace=True, drop=False)
            stockDf.rename(columns={'Date': 'candleTime', 'High': 'high', 'Low': 'low', 'Open': 'start', 'Close': 'close', 'Volume' : 'vol'}, inplace = True)
            stockDf['candleTime'] = stockDf['candleTime'].dt.strftime('%Y-%m-%d')
 
            features =['candleTime', 'start', 'high', 'low', 'close', 'vol']
            stockDf = stockDf[features]
            print(stockDf)
            return stockDf
 
        except:
            print("[%s] Ticker load fail" % ticker)
            return None
    
    def getStocksList(self, limit, debug = False):
        sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        sp500 = sp500[['Security', 'Symbol']] 
        sp500 = sp500.rename(columns={'Security': 'name', 'Symbol': 'code'})
        
        nasdaqDf = pd.read_html("https://en.wikipedia.org/wiki/NASDAQ-100#External_links")[3]
        nasdaqDf = nasdaqDf.rename(columns={'Company': 'name', 'Ticker': 'code'})
 
        stockDf = sp500.append(nasdaqDf)
        stockDf = stockDf.drop_duplicates(['code'], keep='last')
        # 시총 구하기
        marketCapList = []
        ranking = []
        dropIdx = []
        for idx, row in stockDf.iterrows():
            try:
                if debug == False:
                    tickers = row['code']
                    p = web.get_quote_yahoo(tickers)['marketCap']
                    marketCap = int(p.values[0])
                    marketCapList.append(marketCap)
                else:
                    marketCapList.append(idx)
            except:
                dropIdx.append(idx)
                marketCapList.append(0)
                print("[%s][%s] 시총 갖고오기 에러" % (row['name'], row['code']))
        
        rank = 1
        for i in marketCapList:
            ranking.append(rank)
            rank += 1
 
        stockDf['MarketCap'] = marketCapList
        stockDf = stockDf.sort_values(by='MarketCap', ascending=False)
        stockDf['ranking'] = ranking
 
        stockDf.drop(dropIdx, inplace = True)
        if limit > 0:
            stockDf = stockDf[:limit]
        
        print(stockDf)
        return stockDf 
