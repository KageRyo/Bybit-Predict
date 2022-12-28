import numpy as np                  # 用於科學運算的數學套件
import heapq as hq                  # 堆排序相關
import datetime                     # 處理日期和時間的類別和函數
import discord                      # 用於連接 Discord API
import json                         # 處理 JSON 格式資料
import time                         # 處理時間的函數
import pytz                         # 處理時區的函數
from pybit import usdt_perpetual    # 查詢 USDT 永續合約的接口
from pybit import spot              # 查詢實際交易市場的接口

"""
Bybit-Predict 是 CodeRyo 團隊基於 BybitAPI 開發應用於 Discord 上的加密貨幣趨勢機器人，
開源LICENSE：GNU General Public License v2.0

Bybit-Predict is a cryptocurrency trend prediction robot developed by the CodeRyo team based on the BybitAPI for use on Discord. 
open source LICENSE: GNU General Public License v2.0
"""

intents=discord.Intents().all()     # 獲取所有的 Intents 對象
intents.message_content = True      # 允許讀取消息內容

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
trendPower = []          # 多空權勢資料
averagePrice = []        # 每六根K線平均
priceRatio = []          # 每根K線與前兩根K線平均差的比例的資料
trendMarker = []         # 判斷三根K線趨勢轉換的資料
orderStatus = []         # 訂單狀態資料
walletStatus = []        # 錢包狀態資料
wallet = []              # 錢包資料
tradeResult = []         # trade()的回傳資料
retracementText = ['138.2%', '150%', '161.8%', '200%', '238.2%', '261.8%', '300%']  # 回撤比例
fibonacciText = ['0%', '23.6%', '38.2%', '50%', '61.8%', '78.6%', '100%']           # 斐波那契比例

Bybit="https://api.bybit.com"
APIK="your bybit apikey"
APIS="your bybit apis"

def KLineStatus(times,Name): #呼叫實盤K線數據
    try:
        session_unauth = usdt_perpetual.HTTP( #抓取USDT永續合約資料
            endpoint=Bybit,
            api_key=APIK,
            api_secret=APIS
        )
        data=session_unauth.query_kline( #請求K線資料
            symbol=str(Name),
            interval=240, #抓取240分線(四小時)
            limit=1,    #抓取一個K線數據
            from_time=times     #抓取目標K線時間
        )
        try:
            with open("data.json","w") as f:
                json.dump(data,f)
            with open('data.json') as f:
                data=(json.load(f))
                data=data["result"]
            try:
                Kline_data=["open_time","volume","open","high","low","close"]
                Kline=[]
                for i in Kline_data: 
                    Kline.append(data[0][i])  #Kline=[open_time,volume,open,high,low,close]
                return Kline
            except:
                print("拆解data.json資料錯誤")
        except:
            print("建立data.json錯誤")
    except:
        print("請求K線錯誤")
        time.sleep(3)
        KLineStatus(times,Name)

def savedata(Kline):#存取K線資料
    try:
        print(Kline)
        openTime.append(Kline[0]) 
        volume.append(Kline[1])
        open.append(Kline[2])
        high.append(Kline[3])
        low.append(Kline[4])
        close.append(Kline[5])
        return 1
    except:
        print("儲存K線資料錯誤")
        return 0

def PB(T): #回推K線
    try:
        x=0
        while x < T:
            amount=abc(open[x],high[x],low[x],close[x])
            if amount==1:
                powerUP(volume[x])
            if amount==0:
                powerDOWN(volume[x])
            x+=1
    except:
        print("回推K線錯誤")

def AAA(): #計算每六根K線的平均
    try:
        averagePrice = []
        for i in range(0, len(volume), 6):
            averagePrice.append(np.average(volume[i:i+6]))

        priceRatio = []
        for i in range(2, len(averagePrice)):
            priceRatio.append((np.average(averagePrice[i-2:i]) - averagePrice[i]) / averagePrice[i])

        trendMarker = [1 if ratio > 0 else 0 for ratio in priceRatio]

        initial_trend_length = len(trendMarker) - len(trendMarker[trendMarker[0]:])
        print(initial_trend_length)
        PB(initial_trend_length * 6)
    except:
        print("計算六根平均K線錯誤")

def Variation(openTime,open,close): #計算時間線
    try:
        difference=[]
        timerange=[]
        futuretime=[]
        for x in range(42):
            difference.append(abs(open[x]-close[x]))
        max =map(difference.index,hq.nlargest(2,difference))
        for x in list(max):
            timerange.append(openTime[x])
        if timerange[0] > timerange[1]:
            MAX1=timerange[0]
        else:
            MAX1=timerange[1]
        TR=abs(timerange[0]-timerange[1])
        R=[138.2,150,161.8,200,238.2,261.8,300]
        for t in R:
            futuretime.append(TR*t/100)
        for x in range(0,7):
            print(Ktime(MAX1+(int(futuretime[x]/14400)*14400)+28800),"\t",R[x],"%")
            W=Ktime(MAX1+(int(futuretime[x]/14400)*14400)+28800)
            recommendedTime.append(W)
    except:
        print("計算時間線錯誤")

def Wtime(): #換算UTC為秒
    try:
        tz = pytz.timezone( 'Europe/London' )   #設置時區為UTC+0
        timeString  =  datetime.datetime.now(tz).strftime( "%Y-%m-%d %H:%M:%S" )
        struct_time = time.strptime(timeString, "%Y-%m-%d %H:%M:%S")
        time_stamp = int(time.mktime(struct_time))
        return time_stamp
    except:
        print("換算UTC為秒錯誤")

def Ktime(time_stamp): #換算秒為UTC
    try:
        struct_time=time.localtime(time_stamp)
        timeString = time.strftime("%Y-%m-%d %H:%M:%S", struct_time)
        return timeString
    except:
        print("換算秒為UTC錯誤")

def abc(open,high,low,close): #檢測多空頭
    try:
        a=0
        b=0
        c=0
        d=0
        e=0
        if close > open:
            if abs(high-close)>abs((open-close)*4):
                #print("長上引線")
                a=1
            if abs(open-low)>abs((open-close)*4):
                #print("長下引線")
                b=1
        if close < open:
            if abs(high-open)>abs((open-close)*4):
                #print("長上引線")
                a=1
            if abs(close-low)>abs((open-close)*4):
                #print("長下引線")
                b=1
        if (open == high) and (high == low) and (low == close):             #垃圾標才會出現的K線狀態
            c=1
        if a==1 and b==1 :
            #print("十字線")
            c=1
        if (close > open and a!=1) or b==1:
            #print("多頭收線")
            d=1
        if (close < open and b!=1) or a==1:
            #print("空頭收線")
            e=1
        if ((a==1 or e==1) and c==0):
            #print("做空")
            trendType.append("空頭")
            return 0
        if ((b==1 or d==1) and c==0):
            #print("做多")
            trendType.append("多頭")
            return 1
        if(c==1):
            trendType.append("十字線")
            return None
    except:
        print("檢測多空頭錯誤")

def powerUP(volume): #計算多頭量能
    try:
        if volume!=None:
            bullK.append(volume)
            print("多頭"+str(bullK))
        if volume==None:
            t=0
            x=0
            UPtotal=0
            if len(bullK) != 0:
                while x<len(bullK):
                    if bullK[x]>=np.average(bullK): #求大於KK平均得值
                        UPtotal=UPtotal+bullK[x]
                        t+=1
                    x+=1
                UPaverage=UPtotal/t
                if UPaverage==0:
                    return 0
                else:
                    return UPaverage
            else:
                return 0
    except:
        print("計算多頭量能錯誤")

def powerDOWN(volume): #計算空頭量能
    try:
        if volume!=None:
            bearK.append(volume)
            print("空頭"+str(bearK))
        if volume==None:
            t=0
            x=0
            DOWNtotal=0
            DOWNaverage=0
            if len(bearK) != 0:
                while x<len(bearK):
                    if bearK[x]>=np.average(bearK):
                        DOWNtotal=DOWNtotal+bearK[x]
                        t+=1
                    x+=1
                DOWNaverage=DOWNtotal/t
                if DOWNaverage==0:
                    return 0
                else:
                    return DOWNaverage
            else:
                return 0
    except:
        print("計算空頭量能錯誤")

def Compare(UP,DOWN): #比較多空權勢
    try:
        if UP > ((DOWN*0.2)+DOWN):
            print("多頭強勢")
            trendPower.append("多頭強勢")
            return 1
        elif DOWN > ((UP*0.2)+UP):
            print("空頭強勢")
            trendPower.append("空頭強勢")
            return 0
        else:
            print("多空均衡")
            trendPower.append("多空均衡")
            return None
    except:
        print("比較多空權勢錯誤")

def re(EX): #計算點位
    try:
        H=sorted(close) #排列Close資料由小到大
        Percentile = np.percentile(H,[0,25,50,75,100])  
        IQR = Percentile[3] - Percentile[1] #IQR=上四分位與下四分位的差值
        UpLimit = Percentile[3]+IQR*1.5 #上界=上四分位+1.5倍IQR
        DownLimit = Percentile[1]-IQR*1.5 #下界=下四分位+1.5倍四IQR
        benchmark=((UpLimit+DownLimit)/2)-EX #61.8%
        range=abs(benchmark+(benchmark/2)+(benchmark/16)+(benchmark/32)+(benchmark/64)+(benchmark/128)+(benchmark/1068)) #100.00005%
        if EX == sorted(high,reverse=True)[0]:
            return (EX-range)
        if EX == sorted(low)[0]:
            return (EX+range)
    except:
        print("計算點位錯誤")

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

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print('目前登入身份：',bot.user)
    game = discord.Game('預測機器人')
    #discord.Status.<狀態>，可以是online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.online, activity=game)

@bot.event
#當有訊息時
async def on_message(message):
    channel=bot.get_channel(your discrod chat channel)
    keyword=['BTCUSDT','SOLUSDT','GMTUSDT','MATICUSDT','BELUSDT',
             'UNFIUSDT','XRPUSDT','SANDUSDT','AVAXUSDT','ADAUSDT',
             'LINKUSDT','AAVEUSDT','ATOMUSDT','XTZUSDT','NEARUSDT',
             'CHZUSDT','APEUSDT','UNIUSDT','GALAUSDT','BNBUSDT',
             'DOTUSDT','SHIB1000USDT','SRMUSDT','LTCUSDT','FTMUSDT',
             'RUNEUSDT','OGNUSDT','LUNA2USDT','STORJUSDT','AXSUSDT',
             'XMRUSDT','ETHUSDT']
    ID=message.content

    if message.content in keyword and message.author and message.channel == channel:
        await message.channel.send(ID+"預測中請稍後")
        print(ID)
        if predict(ID) == 1 :
            embed=discord.Embed(title=ID+"預測結果",color=0x7ceefd)
            embed.add_field(name="多空權勢", value=trendPower[0], inline=False)
            if Compare(powerUP(None),powerDOWN(None)) != None:
                embed.add_field(name="------------------------------------------------------------------------", value="建議開單點位", inline=False)
                embed.add_field(name=fibonacciText[0], value=recommendedPosition[0], inline=True)
                embed.add_field(name=fibonacciText[1], value=recommendedPosition[1], inline=True)
                embed.add_field(name=fibonacciText[2], value=recommendedPosition[2], inline=True)
                embed.add_field(name=fibonacciText[3], value=recommendedPosition[3], inline=True)
                embed.add_field(name=fibonacciText[4], value=recommendedPosition[4], inline=True)
                embed.add_field(name=fibonacciText[5], value=recommendedPosition[5], inline=True)
                embed.add_field(name=fibonacciText[6], value=recommendedPosition[6], inline=True)  
            embed.add_field(name="-----------------------------------------------------------------------", value="建議開單時間", inline=False)
            embed.add_field(name=retracementText[0], value=recommendedTime[0], inline=False)
            embed.add_field(name=retracementText[1], value=recommendedTime[1], inline=False)
            embed.add_field(name=retracementText[2], value=recommendedTime[2], inline=False)
            embed.add_field(name=retracementText[3], value=recommendedTime[3], inline=False)
            embed.add_field(name=retracementText[4], value=recommendedTime[4], inline=False)
            embed.add_field(name=retracementText[5], value=recommendedTime[5], inline=False)
            embed.add_field(name=retracementText[6], value=recommendedTime[6], inline=False)
            await message.channel.send(embed=embed)
            recommendedPosition.clear()
            recommendedTime.clear()
            trendPower.clear()
            bullK.clear()
            bearK.clear()
            trendType.clear()
            openTime.clear()
            volume.clear()
            open.clear()
            high.clear()
            low.clear()
            close.clear()
            averagePrice.clear()
            priceRatio.clear()
            trendMarker.clear()
        elif predict(ID) == 0:
            recommendedPosition.clear()
            recommendedTime.clear()
            trendPower.clear()
            bullK.clear()
            bearK.clear()
            trendType.clear()
            openTime.clear()
            volume.clear()
            open.clear()
            high.clear()
            low.clear()
            close.clear()
            averagePrice.clear()
            priceRatio.clear()
            trendMarker.clear()
            await message.channel.send("錯誤無法預測")

bot.run("your discord bot token")
