import numpy as np                  # 用於科學運算的數學套件
import heapq as hq                  # 堆排序相關
import datetime                     # 處理日期和時間的類別和函數
import json                         # 處理 JSON 格式資料
import time                         # 處理時間的函數
from pytz import timezone           # 處理時區的函數
from pybit import usdt_perpetual    # 查詢 USDT 永續合約的接口
from pybit import spot              # 查詢實際交易市場的接口