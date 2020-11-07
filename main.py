### 라이브러리 설치
# python -m pip install --upgrade pip

### 필요 라이브러리들
# pip install pandas pandas-datareader dataframe
# pip install psutil requests schedule telepot yfinance beautifulsoup4 plotly  

### 딥러닝에 필요한 것들
# pip install tensorflow keras matplotlib astroid==2.2.5 pylint==2.3.1

### 윈도우에서 talib 설치시 아래 링크에서 파이썬 버젼에 맞는 (cpXX-amd64)로 다운 받아서 해줘야 한다.
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# pip install .\TA_Lib-0.4.19-cp38-cp38-win_amd64.whl

# 리눅스에선 그냥 
# pip install ta-lib
# 안될경우 리눅스에서 설치법
# $ wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
# $ tar -xvf ta-lib-0.4.0-src.tar.gz 
# $ cd ta-lib
# $ ./configure --prefix=/usr
# $ make

# 이 프로그램 설계
# 1. 웹에서 인기 있는 종목 수집 (거래량 순)
# 2. 웹에서 데이터 수집 (한국 주식 / 미국 주식)
# 3. 전략 테스팅 매수 / 매도 시스널 포착
# 4. 3에서 포착된 주식 차트 그리고 텔레그램으로 전송

import os
import time
import signal
import sys

import botConfig
from bot import Bot

def test(bot):
    bot.getStocksList()
    bot.checkStrategy()

def signalHandler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)
#-----------------------------------------
# 메인 함수 시작
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signalHandler)
    
    usaBot = Bot(botConfig.USABotConfig())
    koreaBot = Bot(botConfig.KoreaBotConfig())

    test(usaBot)
    test(koreaBot)

    botList = []
    botList.append(usaBot)
    botList.append(koreaBot)

    while(True):
        now = time.localtime()
        if now.tm_wday < 6:  ## 일요일은 안함
            for bot in botList:
                bot.do()

        current = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        print("지금시간 : [%s]" % current)
        time.sleep(60)

    