import imports as ipk

""" 
Bybit-Predict 是 CodeRyo 團隊基於 BybitAPI 開發應用於 Discord 上的加密貨幣趨勢機器人，
開源LICENSE：GNU General Public License v2.0
Bybit-Predict is a cryptocurrency trend prediction robot developed by the CodeRyo team based on the BybitAPI for use on Discord. 
open source LICENSE: GNU General Public License v2.0
"""

bullK = []               # 高於平均的多頭K線
bearK = []               # 高於平均的空頭K線
trendType = []           # 紀錄多空頭與十字線
openTime = []            # K線時間戳資料
klineOpen = []           # K線開盤價資料
klineHigh = []           # K線最高價資料
klineLow = []            # K線最低價資料
klineClose = []          # K線收盤價資料
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

# 讀取 config.json 的設定檔案
with open("config.json") as f:
    config=ipk.json.load(f)
    APIK=config['bybit_api_key']
    APIS=config['bybit_api_secret']

# 用於呼叫各方法的主要程式
def predict(ID):
    try:
        se=0
        x=0
        while x<180:
            while True:
                if saveData(klineStatus(utcToTimestamp()-se,ID))==1:
                    break
            se+=14400
            ipk.time.sleep(0.02)
            x+=1
        calcAverage()
        calcPercentiles(compare(calcPowerUp(None),calcPowerDown(None)))
        variation(openTime,klineOpen,klineClose)
        return 1
    except Exception as e:
        print(e)
        return 0

# 呼叫實盤 K 線數據
def klineStatus(times,coin): 
    try:
        session_unauth = ipk.usdt_perpetual.HTTP( #抓取USDT永續合約資料
            # 如果您希望使用測試網請記得更改endpoint的連結
            endpoint="https://api.bybit.com",
            api_key=APIK,
            api_secret=APIS
        )
        data=session_unauth.query_kline( #請求K線資料
            symbol=str(coin),
            interval=240,       #抓取240分線(四小時)
            limit=1,            #抓取一個K線數據
            from_time=times     #抓取目標K線時間
        )
        try:
            with open("data.json","w") as f:
                ipk.json.dump(data,f,indent=2)
            with open('data.json') as f:
                data=(ipk.json.load(f))
                data=data["result"]
            try:
                Kline_data=["open_time","volume","open","high","low","close"]
                Kline=[]
                for i in Kline_data: 
                    Kline.append(data[0][i])  #Kline=[open_time,volume,open,high,low,close]
                return Kline
            except Exception as e:
                print(e)
                print("拆解data.json資料錯誤")
        except Exception as e:
            print(e)
            print("建立data.json錯誤")
    except Exception as e:
        print(e)
        print("請求K線錯誤")
        ipk.time.sleep(3)
        klineStatus(times,coin)

# 存取 K 線資料
def saveData(Kline):
    try:
        print(Kline)
        openTime.append(Kline[0]) 
        volume.append(Kline[1])
        klineOpen.append(Kline[2])
        klineHigh.append(Kline[3])
        klineLow.append(Kline[4])
        klineClose.append(Kline[5])
        return 1
    except Exception as e:
        print(e)
        print("儲存K線資料錯誤")
        return 0

# 回推 K 線
def backTestKline(T):
    try:
        x=0
        while x < T:
            amount=checkTrend(klineOpen[x],klineHigh[x],klineLow[x],klineClose[x])
            if amount==1:
                calcPowerUp(volume[x])
            if amount==0:
                calcPowerDown(volume[x])
            x+=1
    except Exception as e:
        print(e)
        print("回推K線錯誤")

# 計算每六根 K 線的平均
def calcAverage():
    try:
        averagePrice = []
        for i in range(0, len(volume), 6):
            averagePrice.append(ipk.np.average(volume[i:i+6]))

        priceRatio = []
        for i in range(2, len(averagePrice)):
            priceRatio.append((ipk.np.average(averagePrice[i-2:i]) - averagePrice[i]) / averagePrice[i])

        trendMarker = [1 if ratio > 0 else 0 for ratio in priceRatio]

        initial_trend_length = len(trendMarker) - len(trendMarker[trendMarker[0]:])
        print(initial_trend_length)
        backTestKline(initial_trend_length * 6)
    except Exception as e:
        print(e)
        print("計算六根平均K線錯誤")

# 計算時間線
def variation(openTime,open,close): 
    try:
        difference=[]
        timerange=[]
        futuretime=[]
        for x in range(42):
            difference.append(abs(open[x]-close[x]))
        max =map(difference.index,ipk.hq.nlargest(2,difference))
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
            print(timestampToUtc(MAX1+(int(futuretime[x]/14400)*14400)+28800),"\t",R[x],"%")
            W=timestampToUtc(MAX1+(int(futuretime[x]/14400)*14400)+28800)
            recommendedTime.append(W)
    except Exception as e:
        print(e)
        print("計算時間線錯誤")

# 換算 UTC 為秒時間戳
def utcToTimestamp(): 
    try:
        tz = ipk.timezone( 'Europe/London' )   #設置時區為UTC+0
        timeString  =  ipk.datetime.datetime.now(tz).strftime( "%Y-%m-%d %H:%M:%S" )
        struct_time = ipk.time.strptime(timeString, "%Y-%m-%d %H:%M:%S")
        time_stamp = int(ipk.time.mktime(struct_time))
        return time_stamp
    except Exception as e:
        print(e)
        print("換算UTC為秒錯誤")

# 換算秒時間戳為 UTC
def timestampToUtc(time_stamp): 
    try:
        struct_time=ipk.time.localtime(time_stamp)
        timeString =ipk.time.strftime("%Y-%m-%d %H:%M:%S", struct_time)
        return timeString
    except Exception as e:
        print(e)
        print("換算秒為UTC錯誤")

# 檢測為多頭或空頭
def checkTrend(open,high,low,close): 
    try:
        a=0
        b=0
        c=0
        d=0
        e=0
        # 如果收盤價大於開盤價
        if close > open:
            # 長上引線
            if abs(high-close)>abs((open-close)*4):
                a=1
            # 長下引線
            if abs(open-low)>abs((open-close)*4):
                b=1
        # 如果收盤價小於開盤價
        if close < open:
            if abs(high-open)>abs((open-close)*4):
                # 長上引線
                a=1
            if abs(close-low)>abs((open-close)*4):
                # 長下引線
                b=1
        # 不良標的會出現的狀況
        if (open == high) and (high == low) and (low == close):
            c=1
        # 十字線
        if a==1 and b==1 :
            c=1
        # 多頭收線
        if (close > open and a!=1) or b==1:
            d=1
        # 空頭收線
        if (close < open and b!=1) or a==1:
            e=1
        # 適合做空
        if ((a==1 or e==1) and c==0):
            trendType.append("空頭")
            return 0
        # 適合做多
        if ((b==1 or d==1) and c==0):
            trendType.append("多頭")
            return 1
        # 十字線
        if(c==1):
            trendType.append("十字線")
            return None
    except Exception as e:
        print(e)
        print("檢測多空頭錯誤")

# 計算多頭量能
def calcPowerUp(volume):
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
                    if bullK[x]>=ipk.np.average(bullK): #求大於 bullK 平均的值
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
    except Exception as e:
        print(e)
        print("計算多頭量能錯誤")

# 計算空頭量能
def calcPowerDown(volume): 
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
                    if bearK[x]>=ipk.np.average(bearK):
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
    except Exception as e:
        print(e)
        print("計算空頭量能錯誤")

# 比較多空權勢
def compare(UP,DOWN): 
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
    except Exception as e:
        print(e)
        print("比較多空權勢錯誤")

# 計算百分位數
def calcPercentiles(com):
    if com==1:
        arry = ipk.np.array([sorted(klineLow)[0],calcPosition(sorted(klineLow)[0])])
        FIV=[0,23.6,38.2,50,61.8,78.6,100]
        for x in range(0,7):
            print(int(ipk.np.percentile(arry,FIV[x])*10000)/10000,"\t\t",FIV[x],"%")
            W=int(ipk.np.percentile(arry,FIV[x])*10000)/10000
            recommendedPosition.append(W)
    if com==0:
        arry = ipk.np.array([calcPosition(sorted(klineHigh,reverse=True)[0]),sorted(klineHigh,reverse=True)[0]])
        FIV=[100,78.6,61.8,50,38.2,23.6,0]
        for x in range(0,7):
            print(int(ipk.np.percentile(arry,FIV[x])*10000)/10000,"\t\t",FIV[x],"%")
            W=int(ipk.np.percentile(arry,FIV[x])*10000)/10000
            recommendedPosition.append(W)

# 計算點位
def calcPosition(EX):
    try:
        H=sorted(klineClose) #排列Close資料由小到大
        Percentile = ipk.np.percentile(H,[0,25,50,75,100])  
        IQR = Percentile[3] - Percentile[1] #IQR=上四分位與下四分位的差值
        UpLimit = Percentile[3]+IQR*1.5 #上界=上四分位+1.5倍IQR
        DownLimit = Percentile[1]-IQR*1.5 #下界=下四分位+1.5倍四IQR
        benchmark=((UpLimit+DownLimit)/2)-EX #61.8%
        range=abs(benchmark+(benchmark/2)+(benchmark/16)+(benchmark/32)+(benchmark/64)+(benchmark/128)+(benchmark/1068)) #100.00005%
        if EX == sorted(klineHigh,reverse=True)[0]:
            return (EX-range)
        if EX == sorted(klineLow)[0]:
            return (EX+range)
    except Exception as e:
        print(e)
        print("計算點位錯誤")

# 清除 list 內的資料
def dataClear():
    recommendedPosition.clear()
    recommendedTime.clear()
    trendPower.clear()
    bullK.clear()
    bearK.clear()
    trendType.clear()
    openTime.clear()
    volume.clear()
    klineOpen.clear()
    klineHigh.clear()
    klineLow.clear()
    klineClose.clear()
    averagePrice.clear()
    priceRatio.clear()
    trendMarker.clear()