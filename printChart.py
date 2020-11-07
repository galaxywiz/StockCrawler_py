# 주식 차트를 그리는 클래스
import numpy as np
import pandas as pd
import dataframe

import datetime
import plotly.graph_objects as go
import tracemalloc
import matplotlib.pyplot as plt

import os
from stockData import StockData

class PrintChart:
    def saveFigure(self, dir, sd):
        try:
            plt.style.use('fivethirtyeight')
            plt.rc('font', family='Droid Sans')
            
            title = "[%s] close price" % (sd.name_) 
            plt.title(title)
            
            plt.figure(figsize=(16,8))
            dataCount = 100
            indi = sd.chartData_.tail(dataCount)
            df = pd.DataFrame(indi)
            df['candleTime'] = pd.to_datetime(df['candleTime'], format='%Y-%m-%d', infer_datetime_format=True)
            df = df.set_index('candleTime')

            plt.xlabel('candleTime', fontsize=18)
            #plt.xticks(rotation=45)
            plt.ylabel('Close Price', fontsize=18)
            plt.scatter(df.index, df['BuySignal'], color='green', label = 'buy', marker='^', alpha=1)
            plt.scatter(df.index, df['SellSignal'], color='red', label = 'sell', marker='v', alpha=1)
            plt.plot(df['close'], label='Close Price', alpha=0.35)
            plt.legend(loc='upper left')
            
            filename = "flg_%s.png" % (sd.code_)
            if os.path.exists(dir) == False:
                os.makedirs(dir)

            p = os.getcwd()
            filePath = "%s/%s%s" % (p, dir, filename)
            if os.path.isfile(filePath) == True:
                os.remove(filePath)
            
            plt.savefig(filePath)

            print("$ 차트 갱신 [%s] => [%s]" % (sd.name_, filename))
            return filePath
        except:
            print("$ 차트 갱신 실패 [%s]" % (sd.name_))
            return None
      