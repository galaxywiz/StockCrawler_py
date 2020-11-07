import pandas as pd 
import dataframe
import sqlite3
from datetime import datetime
from datetime import timedelta
import time
import os

from stockData import StockData
from sqliteDB import SqliteDB

class DayPriceDB(SqliteDB):
    def initDB(self, dbName, tableName):
        super().initDB(dbName, tableName)

        self.tableStruct_ = "candleTime DATETIME PRIMARY KEY, start INT, high INT, low INT, close INT, vol INT"
        self.columns_ = ['candleTime', 'start', 'high', 'low', 'close', 'vol']

class DayPriceFloatDB(SqliteDB):
    def initDB(self, dbName, tableName):
        super().initDB(dbName, tableName)

        self.tableStruct_ = "candleTime DATETIME PRIMARY KEY, start Float, high Float, low Float, close Float, vol INT"
        self.columns_ = ['candleTime', 'start', 'high', 'low', 'close', 'vol']

