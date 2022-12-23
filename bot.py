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