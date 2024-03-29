import numpy as np                     # 用於科學運算的數學套件
import heapq as hq                     # 堆排序相關
import datetime                        # 處理日期和時間的類別和函數
import json                            # 處理 JSON 格式資料
import time                            # 處理時間的函數
from pytz import timezone              # 處理時區的函數
from pybit.unified_trading import HTTP # 查詢合約的接口

""" 
Bybit-Predict 是 CodeRyo 團隊基於 BybitAPI 開發應用於 Discord 上的加密貨幣趨勢機器人，
開源LICENSE：GNU General Public License v2.0
Bybit-Predict is a cryptocurrency trend prediction robot developed by the CodeRyo team based on the BybitAPI for use on Discord. 
open source LICENSE: GNU General Public License v2.0
"""
