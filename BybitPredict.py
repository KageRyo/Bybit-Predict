import discord
import numpy as np
from pybit import usdt_perpetual
import json
import time
import datetime
import pytz
import heapq as hq
from pybit import spot

intents=discord.Intents.default()
intents=discord.Intents().all()
intents.message_content = True

KK=[] #高於平均隻多頭K線
SS=[] #高於平均隻空頭K線
TT=[] #紀錄多空頭與十字線
Open_time=[] #K線Open_time資料
volume=[] #K線volume資料
Open=[] #K線Open資料
High=[] #K線High資料
Low=[] #K線Low資料
Close=[] #K線Close資料
Rtext=['138.2%','150%','161.8%','200%','238.2%','261.8%','300%']
Ftext=['0%','23.6%','38.2%','50%','61.8%','78.6%','100%']
P=[] #建議開單點位資料
FT=[] #建議開單時間資料
txt=[] #多空權勢資料
OP=[] #每六根K線平均
OPXP=[]#每根K線與前兩根K線平均差的比例的資料
PM=[]#判斷三根K線趨勢轉換的資料
OSdata=[]#訂單狀態資料
wallet=[]#錢包狀態資料
money=[]#錢包資料
wall=[]#trade()的回傳資料
Bybit="https://api.bybit.com"
APIK="enter your apikey"
APIS="enter your apiskey"
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
                    Kline.append(K)   #Kline=[Open_time,volume,open,high,low,close]
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
        Open_time.append(Kline[0]) 
        volume.append(Kline[1])
        Open.append(Kline[2])
        High.append(Kline[3])
        Low.append(Kline[4])
        Close.append(Kline[5])
        return 1
    except:
        print("儲存K線資料錯誤")
        return 0

def PB(T): #回推K線
    try:
        x=0
        while x < T:
            amount=abc(Open[x],High[x],Low[x],Close[x])
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
                OP.append(np.average(O))
                O.clear()
                O.append(x)
            else:
                O.append(x) 
        OP.append(np.average(O))
        O.clear()
        for x in range(0,int(len(volume)/6)):#計算每根K線與前兩根K線平均差的比例
            if x==0:
                None
            elif x==1:
                OPXP.append((OP[0]-OP[1])/OP[1])
            elif x==2:
                OPXP.append(((OP[0]+OP[1])/2-OP[2])/OP[2])
            elif x==3:
                OPXP.append(((OP[0]+OP[1]+OP[2])/3-OP[3])/OP[3])
            elif x==4:
                OPXP.append(((OP[0]+OP[1]+OP[2]+OP[3])/4-OP[4])/OP[4])
            else:
                OPXP.append((((OP[x-1]+OP[x-2]+OP[x-3]+OP[x-4]+OP[x-5])/5)-OP[x])/OP[x])
        for x in OPXP : #判斷趨勢轉換
            if x > 0 :
                PM.append(1) #上升
            else:
                PM.append(0) #下降
        L=0
        for x in PM:
            if x == PM[0]:
                L+=1
            else:
                break
        print(L)
        PB(L*6) 
    except:
        print("計算六根平均K線錯誤")

def Variation(Open_time,Open,Close): #計算時間線
    try:
        difference=[]
        timerange=[]
        futuretime=[]
        for x in range(42):
            difference.append(abs(Open[x]-Close[x]))
        max =map(difference.index,hq.nlargest(2,difference))
        for x in list(max):
            timerange.append(Open_time[x])
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
            FT.append(W)
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
            TT.append("空頭")
            return 0
        if ((b==1 or d==1) and c==0):
            #print("做多")
            TT.append("多頭")
            return 1
        if(c==1):
            TT.append("十字線")
            return None
    except:
        print("檢測多空頭錯誤")

def powerUP(volume): #計算多頭量能
    try:
        if volume!=None:
            KK.append(volume)
            print("多頭"+str(KK))
        if volume==None:
            t=0
            x=0
            UPtotal=0
            if len(KK) != 0:
                while x<len(KK):
                    if KK[x]>=np.average(KK): #求大於KK平均得值
                        UPtotal=UPtotal+KK[x]
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
            SS.append(volume)
            print("空頭"+str(SS))
        if volume==None:
            t=0
            x=0
            DOWNtotal=0
            DOWNaverage=0
            if len(SS) != 0:
                while x<len(SS):
                    if SS[x]>=np.average(SS):
                        DOWNtotal=DOWNtotal+SS[x]
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
            txt.append("多頭強勢")
            return 1
        elif DOWN > ((UP*0.2)+UP):
            print("空頭強勢")
            txt.append("空頭強勢")
            return 0
        else:
            print("多空均衡")
            txt.append("多空均衡")
            return None
    except:
        print("比較多空權勢錯誤")

def re(EX): #計算點位
    try:
        H=sorted(Close) #排列Close資料由小到大
        Percentile = np.percentile(H,[0,25,50,75,100])  
        IQR = Percentile[3] - Percentile[1] #IQR=上四分位與下四分位的差值
        UpLimit = Percentile[3]+IQR*1.5 #上界=上四分位+1.5倍IQR
        DownLimit = Percentile[1]-IQR*1.5 #下界=下四分位+1.5倍四IQR
        benchmark=((UpLimit+DownLimit)/2)-EX #61.8%
        range=abs(benchmark+(benchmark/2)+(benchmark/16)+(benchmark/32)+(benchmark/64)+(benchmark/128)+(benchmark/1068)) #100.00005%
        if EX == sorted(High,reverse=True)[0]:
            return (EX-range)
        if EX == sorted(Low)[0]:
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
            arry = np.array([sorted(Low)[0],re(sorted(Low)[0])])
            FIV=[0,23.6,38.2,50,61.8,78.6,100]
            for x in range(0,7):
                print(int(np.percentile(arry,FIV[x])*10000)/10000,"\t\t",FIV[x],"%")
                W=int(np.percentile(arry,FIV[x])*10000)/10000
                P.append(W)
        if com==0:
            arry = np.array([re(sorted(High,reverse=True)[0]),sorted(High,reverse=True)[0]])
            FIV=[100,78.6,61.8,50,38.2,23.6,0]
            for x in range(0,7):
                print(int(np.percentile(arry,FIV[x])*10000)/10000,"\t\t",FIV[x],"%")
                W=int(np.percentile(arry,FIV[x])*10000)/10000
                P.append(W)
        Variation(Open_time,Open,Close)
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
    channel=bot.get_channel(995959711776112683)
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
            embed.add_field(name="多空權勢", value=txt[0], inline=False)
            if Compare(powerUP(None),powerDOWN(None)) != None:
                embed.add_field(name="------------------------------------------------------------------------", value="建議開單點位", inline=False)
                embed.add_field(name=Ftext[0], value=P[0], inline=True)
                embed.add_field(name=Ftext[1], value=P[1], inline=True)
                embed.add_field(name=Ftext[2], value=P[2], inline=True)
                embed.add_field(name=Ftext[3], value=P[3], inline=True)
                embed.add_field(name=Ftext[4], value=P[4], inline=True)
                embed.add_field(name=Ftext[5], value=P[5], inline=True)
                embed.add_field(name=Ftext[6], value=P[6], inline=True)  
            embed.add_field(name="-----------------------------------------------------------------------", value="建議開單時間", inline=False)
            embed.add_field(name=Rtext[0], value=FT[0], inline=False)
            embed.add_field(name=Rtext[1], value=FT[1], inline=False)
            embed.add_field(name=Rtext[2], value=FT[2], inline=False)
            embed.add_field(name=Rtext[3], value=FT[3], inline=False)
            embed.add_field(name=Rtext[4], value=FT[4], inline=False)
            embed.add_field(name=Rtext[5], value=FT[5], inline=False)
            embed.add_field(name=Rtext[6], value=FT[6], inline=False)
            await message.channel.send(embed=embed)
            P.clear()
            FT.clear()
            txt.clear()
            KK.clear()
            SS.clear()
            TT.clear()
            Open_time.clear()
            volume.clear()
            Open.clear()
            High.clear()
            Low.clear()
            Close.clear()
            OP.clear()
            OPXP.clear()
            PM.clear()
        elif predict(ID) == 0:
            P.clear()
            FT.clear()
            txt.clear()
            KK.clear()
            SS.clear()
            TT.clear()
            Open_time.clear()
            volume.clear()
            Open.clear()
            High.clear()
            Low.clear()
            Close.clear()
            OP.clear()
            OPXP.clear()
            PM.clear()
            await message.channel.send("錯誤無法預測")

bot.run("enter your discord bot token")
