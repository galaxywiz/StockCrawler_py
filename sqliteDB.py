import pandas as pd 
import dataframe
import sqlite3
import datetime
import os

class SqliteDB:
    def __init__(self, dbName, tableName):
        self.tableStruct_ = ""
        self.columns_ = []
        self.initDB(dbName, tableName)

    def initDB(self, dbName, tableName):
        dir = "DB/"
        if os.path.exists(dir) == False:
            os.makedirs(dir)
        self.conn_ = sqlite3.connect(dir + dbName)
        self.dbName_ = dbName
        self.tableName_ = tableName

    def _tableName(self, code):
        code = code.replace("=","_")
        name = "%s_%s" % (self.tableName_, code)
        return name

    #----------------------------------------------------------#
    # 테이블이 있는지 확인하고, 있으면 -1, 없으면 0, 생성했으면 1
    def getTable(self, code):
        if self.checkTable(code) == False:
            if self.createTable(code) == False:
                return 0
            else:
                return 1
        return -1

    # 테이블 이름이 있는지 확인
    def checkTable(self, code):
        tableName = self._tableName(code)
        with self.conn_:
            cur = self.conn_.cursor()
            sql = "SELECT count(*) FROM sqlite_master WHERE Name = \'%s\'" % tableName
            cur.execute(sql)
            rows = cur.fetchall()
            for row in rows:          
                if str(row[0]) == "1":
                    return True
            return False
    
    
    # 테이블 생성
    def createTable(self, code):
        tableName = self._tableName(code)
        with self.conn_:
            try:
                cur = self.conn_.cursor()
                sql = "CREATE TABLE %s (%s);" % (tableName, self.tableStruct_)
                cur.execute(sql)
                return True
            except:
                log = "! [%s] table make fail" % tableName 
                print(log)
                return False
    
    # 데이터 저장
    def save(self, code, dataframe):    
        tableName = self._tableName(code)
        with self.conn_:
            try:
                cur = self.conn_.cursor()
                columns = ""
                value = ""
                for col in self.columns_:
                    if len(columns) == 0:
                        columns = col
                    else:
                        columns = "%s, '%s'" % (columns, col)

                    if len(value) == 0:
                        value = "?"
                    else:
                        value = "%s, ?" % (value)

                sql = "INSERT OR REPLACE INTO \'%s\' (%s) VALUES(%s)" % (tableName, columns, value)
                cur.executemany(sql, dataframe.values)    
                self.conn_.commit()
            except:
                return None
            
    # 데이터 로드
    def load(self, code, orderBy = "candleTime ASC"):
        tableName = self._tableName(code)
        with self.conn_:
            try:  
                columns = ""
                for col in self.columns_:
                    if len(columns) == 0:
                        columns = col
                    else:
                        columns = "%s, %s" % (columns, col)              

                sql = "SELECT %s FROM \'%s\' ORDER BY %s" % (columns, tableName, orderBy)
                df = pd.read_sql(sql, self.conn_, index_col=None)
                if len(df) == 0:
                    return False, None
            except:
                return False, None

        return True, df     
