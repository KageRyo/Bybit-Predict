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
                data = json.load(f)
            try:
                data=data.get("result")
                da=str(data).strip('{[]}')
                Del="_'!@#$%^&*()\/:*?<>|-+ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
                Kline=[]
                for x in range(6): #擷取需要訊息
                    K = float(''.join( x for x in da.split(', ')[5+x] if x not in Del))
                    Kline.append(K)   #Kline=[openTime,volume,open,high,low,close]
                return Kline
            except:
                print("拆解data.json資料錯誤")
        except:
            print("建立data.json錯誤")
    except:
        print("請求K線錯誤")
        time.sleep(3)
        KLineStatus(times,Name)
def NKLineStatus(Name):
    try:
        session_unauth = spot.HTTP(
            endpoint=Bybit
        )
        data=session_unauth.latest_information_for_symbol(
            symbol=Name
        )
        try:
            with open("Ndata.json","w") as f:
                json.dump(data,f)
            with open('Ndata.json') as f:
                data = json.load(f)
            data=data.get("result")
            try:
                da=str(data).strip('{}')
                Del="_'!@#$%^&*()\/:*?<>|-+ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
                K=[]
                K = float(''.join( x for x in da.split(', ')[6] if x not in Del))
                return K
            except:
                print("拆解Ndata.json資料錯誤")
        except:
            print("建立Ndata.json錯誤")
    except:
        print("請求最新K線錯誤")
        time.sleep(3)
        NKLineStatus(Name)
        

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
        O=[]
        for x in volume:
            if len(O)==6:
                averagePrice.append(np.average(O))
                O.clear()
                O.append(x)
            else:
                O.append(x) 
        averagePrice.append(np.average(O))
        O.clear()
        for x in range(0,int(len(volume)/6)):#計算每根K線與前兩根K線平均差的比例
            if x==0:
                None
            elif x==1:
                priceRatio.append((averagePrice[0]-averagePrice[1])/averagePrice[1])
            elif x==2:
                priceRatio.append(((averagePrice[0]+averagePrice[1])/2-averagePrice[2])/averagePrice[2])
            elif x==3:
                priceRatio.append(((averagePrice[0]+averagePrice[1]+averagePrice[2])/3-averagePrice[3])/averagePrice[3])
            elif x==4:
                priceRatio.append(((averagePrice[0]+averagePrice[1]+averagePrice[2]+averagePrice[3])/4-averagePrice[4])/averagePrice[4])
            else:
                priceRatio.append((((averagePrice[x-1]+averagePrice[x-2]+averagePrice[x-3]+averagePrice[x-4]+averagePrice[x-5])/5)-averagePrice[x])/averagePrice[x])
        for x in priceRatio : #判斷趨勢轉換
            if x > 0 :
                trendMarker.append(1) #上升
            else:
                trendMarker.append(0) #下降
        L=0
        for x in trendMarker:
            if x == trendMarker[0]:
                L+=1
            else:
                break
        print(L)
        PB(L*6) 
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