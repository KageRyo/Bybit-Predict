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
import discord

"""
Bybit-Predict 是 CodeRyo 團隊基於 BybitAPI 開發應用於 Discord 上的加密貨幣趨勢機器人，
開源LICENSE：GNU General Public License v2.0
Bybit-Predict is a cryptocurrency trend prediction robot developed by the CodeRyo team based on the BybitAPI for use on Discord. 
open source LICENSE: GNU General Public License v2.0
"""

def predict(Name): #呼叫各函式進行判斷
    pass

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
trendPower = []          # 多空

"""
在 main.py , bot.py , kline.py , config.json 編輯完成前請先使用 BybitPredict.py 運行。   
"""
