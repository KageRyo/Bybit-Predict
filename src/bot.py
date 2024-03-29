import src.analysis as analysis
import discord
from src.utils import json

""" 
Bybit-Predict 是 CodeRyo 團隊基於 BybitAPI 開發應用於 Discord 上的加密貨幣趨勢機器人，
開源LICENSE：GNU General Public License v2.0
Bybit-Predict is a cryptocurrency trend prediction robot developed by the CodeRyo team based on the BybitAPI for use on Discord. 
open source LICENSE: GNU General Public License v2.0
"""

intents=discord.Intents().all()     # 獲取所有的 Intents 對象
intents.message_content = True      # 允許讀取消息內容

# 讀取 config.json 的設定檔案
with open("src\config.json") as f:
    config=json.load(f)
    token=config['discord_bot_token']
    channelID=int(config['discord_channel_id'])

# Discord 機器人變數設置
bot = discord.Client(intents=intents)
    
# Discord 機器人主程式
def main():
    # Discord 機器人 TOKEN
    bot.run(token)

# Discord 機器人狀態設置
@bot.event
async def on_ready():
    print('目前登入身份：',bot.user)
    game = discord.Game('Bybit-Predict by.CodeRyo')
    # discord.Status.<狀態>，可以是online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.online, activity=game)

# Discord 機器人對訊息事件的程式
@bot.event
async def on_message(message):
    channel=bot.get_channel(channelID) # 指定頻道ID
    # 接收的關鍵詞（如果您想分析的幣不在這裡可自行添加）
    keyword=['BTCUSDT','SOLUSDT','GMTUSDT','MATICUSDT','BELUSDT',
             'UNFIUSDT','XRPUSDT','SANDUSDT','AVAXUSDT','ADAUSDT',
             'LINKUSDT','AAVEUSDT','ATOMUSDT','XTZUSDT','NEARUSDT',
             'CHZUSDT','APEUSDT','UNIUSDT','GALAUSDT','BNBUSDT',
             'DOTUSDT','SHIB1000USDT','SRMUSDT','LTCUSDT','FTMUSDT',
             'RUNEUSDT','OGNUSDT','LUNA2USDT','STORJUSDT','AXSUSDT',
             'XMRUSDT','ETHUSDT']
    ID=message.content

    # 收到訊息後的判斷式
    if message.content in keyword and message.author and message.channel == channel:
        print('收到訊息：',message.content)
        await message.channel.send(ID+"預測中請稍後")
        print(ID)
        result=analysis.predict(ID)
        # 正確完成預測後輸出結果
        if result == 1 :
            embed=discord.Embed(title=ID+"預測結果",color=0x7ceefd)
            embed.add_field(name="多空權勢", value=analysis.trendPower[0], inline=False)
            if analysis.compare(analysis.calcPowerUp(None),analysis.calcPowerDown(None)) != None:
                embed.add_field(name="------------------------------------------------------------------------", value="建議開單點位", inline=False)
                embed.add_field(name=analysis.fibonacciText[0], value=analysis.recommendedPosition[0], inline=True)
                embed.add_field(name=analysis.fibonacciText[1], value=analysis.recommendedPosition[1], inline=True)
                embed.add_field(name=analysis.fibonacciText[2], value=analysis.recommendedPosition[2], inline=True)
                embed.add_field(name=analysis.fibonacciText[3], value=analysis.recommendedPosition[3], inline=True)
                embed.add_field(name=analysis.fibonacciText[4], value=analysis.recommendedPosition[4], inline=True)
                embed.add_field(name=analysis.fibonacciText[5], value=analysis.recommendedPosition[5], inline=True)
                embed.add_field(name=analysis.fibonacciText[6], value=analysis.recommendedPosition[6], inline=True)  
            embed.add_field(name="-----------------------------------------------------------------------", value="建議開單時間", inline=False)
            embed.add_field(name=analysis.retracementText[0], value=analysis.recommendedTime[0], inline=False)
            embed.add_field(name=analysis.retracementText[1], value=analysis.recommendedTime[1], inline=False)
            embed.add_field(name=analysis.retracementText[2], value=analysis.recommendedTime[2], inline=False)
            embed.add_field(name=analysis.retracementText[3], value=analysis.recommendedTime[3], inline=False)
            embed.add_field(name=analysis.retracementText[4], value=analysis.recommendedTime[4], inline=False)
            embed.add_field(name=analysis.retracementText[5], value=analysis.recommendedTime[5], inline=False)
            embed.add_field(name=analysis.retracementText[6], value=analysis.recommendedTime[6], inline=False)
            await message.channel.send(embed=embed)
            analysis.dataClear()
        # 預測失敗時的提示文字
        elif result == 0:
            analysis.dataClear()
            await message.channel.send("錯誤無法預測")

if __name__ == "__main__":
    main()