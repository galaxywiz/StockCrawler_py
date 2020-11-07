# 텐서플로어를 사용해서 주식 데이터를 예측해 보자
# 과거 데이터를 기반으로 패턴을 머신러닝으로 찾아내서
# 이걸 가지고 다음날 데이터를 예측. 
# 물론 미래일은 불확실이므로 정말 맞는건 아니고
# 특별한 이슈가 없으면, 아마 60,70%로 맞을지도 정도
import tensorflow as tf
import numpy as np
import pandas as pd
import datetime
import gc
import os

from stockData import StockData

class StockPredic:
    def __init__(self, stockData):
        # 하이퍼파라미터
        self.seqLength_ = 28              # 1개 시퀀스의 길이(시계열데이터 입력 개수)
        self.epochNum_ = 50             # 에폭 횟수(학습용전체데이터를 몇 회 반복해서 학습할 것인가 입력)
        self.tenserDir_ = "tensorSave/"

        self.stockData_ = stockData
        futureConsidered = ["start", "high", "low", "close"]
        self.priceTable_ = stockData.chartData_[futureConsidered]
        self.inColumnCnt_ = len(futureConsidered)
        self.outputCnt_ = 1          # 결과데이터의 컬럼 개수

        self.priceTable_ = self.priceTable_.values[1:].astype(np.float)

    #----------------------------------------------------------#
    def __modelName(self):
        name = "model_%s" % (self.stockData_.code_)
        return name

    # 너무 작거나 너무 큰 값이 학습을 방해하는 것을 방지하고자 정규화한다
    # x가 양수라는 가정하에 최소값과 최대값을 이용하여 0~1사이의 값으로 변환
    # Min-Max scaling
    def __minMaxScaling(self, x):
        npX = np.asarray(x)
        return (npX - npX.min()) / (npX.max() - npX.min() + 1e-7) # 1e-7은 0으로 나누는 오류 예방차원
    
    # 정규화된 값을 원래의 값으로 되돌린다
    # 정규화하기 이전의 org_x값과 되돌리고 싶은 x를 입력하면 역정규화된 값을 리턴한다
    def __inverseMinMaxScaling(self, orgX, x):
        orgNpX = np.asarray(orgX)
        npX = np.asarray(x)
        return (npX * (orgNpX.max() - orgNpX.min() + 1e-7)) + orgNpX.min()
    
    #----------------------------------------------------------#
    def predic(self, refresh = False):
        try:
            price = self.priceTable_[:, :-1]
            normPrice = self.__minMaxScaling(price)

            volume = self.priceTable_[:, -1:]
            normVol = self.__minMaxScaling(volume)

            x = np.concatenate((normPrice, normVol), axis=1)
            y = x[:, [3]]      ####### close 종가가 타겟 #######

            dataX = [] # 입력으로 사용될 Sequence Data
            dataY = [] # 출력(타켓)으로 사용
    
            for i in range(0, len(y) - self.seqLength_):
                _x = x[i : i + self.seqLength_]
                _y = y[i + self.seqLength_] # 다음 나타날 주가(정답)
                dataX.append(_x) # dataX 리스트에 추가
                dataY.append(_y) # dataY 리스트에 추가

            # 학습용/테스트용 데이터 생성
            # 전체 70%를 학습용 데이터로 사용
            trainSize = int(len(dataY) * 0.7)
            
            # 데이터를 잘라 학습용 데이터 생성
            trainX = np.array(dataX[0:trainSize])
            trainY = np.array(dataY[0:trainSize])
            
            trainX = np.reshape(trainX, (trainX.shape[0], trainX.shape[1], self.inColumnCnt_))

            # 데이터를 잘라 테스트용 데이터 생성
            testX = np.array(dataX[trainSize:len(dataX)])
            testY = np.array(dataY[trainSize:len(dataY)])

            path = self.tenserDir_
            if os.path.exists(path) == False:
                os.makedirs(path)

            savePath = "%s%s.h5" % (path, self.__modelName())

            with tf.device("/cpu:0"):
                if os.path.isfile(savePath) == True:
                    model = tf.keras.models.load_model(savePath)
                    model.summary()
                    print("* %s 모델 로드 [%s] " % (self.stockData_.name_, savePath))
            
                    if refresh:
                        model.fit(trainX, trainY, validation_data=(testX, testY), batch_size=10, epochs=1)
                        model.save(savePath)
                        return 0
                else:
                    model = tf.keras.models.Sequential()
                    model.add(tf.keras.layers.LSTM(256, return_sequences=True, input_shape=(self.seqLength_, self.inColumnCnt_))) # (timestep, feature) 
                    model.add(tf.keras.layers.LSTM(256, return_sequences=False))
                    model.add(tf.keras.layers.Dense(self.outputCnt_, activation='linear'))
                    model.compile(loss='mse', optimizer=tf.keras.optimizers.RMSprop(clipvalue=1.0))
                    model.summary()
                    
                    model.fit(trainX, trainY, validation_data=(testX, testY), batch_size=10, epochs=self.epochNum_)
                    model.save(savePath)

                # sequence length만큼의 가장 최근 데이터를 슬라이싱한다
                recentData = np.array([x[(len(x) - self.seqLength_): ]])
                # 내일 종가를 예측해본다
                testPredict = model.predict(recentData)
                testPredict = self.__inverseMinMaxScaling(price, testPredict) # 금액데이터 역정규화한다
                
                recentData = self.__inverseMinMaxScaling(price, recentData)
            
                tf.keras.backend.clear_session()

            del recentData
            del model
                
            return testPredict[0]

        except:
            print("* %s 모델 예측 에러" % (self.stockData_.name_))
            return 0