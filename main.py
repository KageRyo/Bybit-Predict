import numpy as np                  # 用於科學運算的數學套件
import heapq as hq                  # 堆排序相關
import datetime                     # 處理日期和時間的類別和函數
import discord                      # 用於連接 Discord API
import json                         # 處理 JSON 格式資料
import time                         # 處理時間的函數
import pytz                         # 處理時區的函數
from pybit import usdt_perpetual    # 查詢 USDT 永續合約的接口
from pybit import spot              # 查詢實際交易市場的接口

import kline
import bot

Bybit="https://api.bybit.com"
APIK="your bybit apikey"
APIS="your bybit apis"

def predict(Name): #呼叫各函式進行判斷
    try:
        se=0
        x=0
        while x<180  :
            while True:
                if savedata(KLineStatus(Wtime()-se,Name))==1:
                    break
            se+=14400
            time.sleep(0.1)
            x+=1
        AAA()
        com=Compare(powerUP(None),powerDOWN(None))
        if com==1:
            arry = np.array([sorted(low)[0],re(sorted(low)[0])])
            FIV=[0,23.6,38.2,50,61.8,78.6,100]
            for x in range(0,7):
                print(int(np.percentile(arry,FIV[x])*10000)/10000,"\t\t",FIV[x],"%")
                W=int(np.percentile(arry,FIV[x])*10000)/10000
                recommendedPosition.append(W)
        if com==0:
            arry = np.array([re(sorted(high,reverse=True)[0]),sorted(high,reverse=True)[0]])
            FIV=[100,78.6,61.8,50,38.2,23.6,0]
            for x in range(0,7):
                print(int(np.percentile(arry,FIV[x])*10000)/10000,"\t\t",FIV[x],"%")
                W=int(np.percentile(arry,FIV[x])*10000)/10000
                recommendedPosition.append(W)
        Variation(openTime,open,close)
        return 1
    except:
        return 0

bullK = []               # 高於平均的多頭K線
bearK = []               # 高於平均的空頭K線
trendType = []           # 紀錄多空頭與十字線
openTime = []            # K線時間戳資料
open = []                # K線開盤價資料
high = []                # K線最高價資料
low = []                 # K線最低價資料
close = []               # K線收盤價資料
volume = []              # K線成交量資料
recommendedPosition = [] # 建議開單點位資料
recommendedTime = []     # 建議開單時間資料
trendPower = [] # 多空權勢資料
averagePrice = [] # 每六根K線平均
priceRatio = [] # 每根K線與前兩根K線平均差的比例的資料
trendMarker = [] # 判斷三根K線趨勢轉換的資料
orderStatus = [] # 訂單狀態資料
walletStatus = [] # 錢包狀態資料
wallet = [] # 錢包資料
tradeResult = [] # trade()的回傳資料
retracementText = ['138.2%', '150%', '161.8%', '200%', '238.2%', '261.8%', '300%'] # 回撤比例
fibonacciText = ['0%', '23.6%', '38.2%', '50%', '61.8%', '78.6%', '100%'] # 斐波那契比例

if name == "main":
    pass