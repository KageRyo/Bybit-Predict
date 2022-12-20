# Bybit-Predict
Predict cryptocurrency trends using Python and the Bybit exchange API



---

This code define a function called KLineStatus that retrieves and processes cryptocurrency data from the Bybit API. This function takes in two arguments: times and Name. times is a time parameter that specifies which data to retrieve, and Name is a string that specifies the cryptocurrency pair to retrieve data for.

The function first initializes an unauthenticated HTTP session with the Bybit API using the usdt_perpetual.HTTP function, passing in the Bybit API endpoint URL, the API key, and the API secret as arguments. It then calls the query_kline method on this session to request K-line data for the specified cryptocurrency pair. The interval parameter is set to 240, which corresponds to a 4-hour time interval, and the limit parameter is set to 1, which retrieves only one data point. The from_time parameter is set to the value of the times argument, which specifies the time to retrieve data for.

The function then processes the retrieved data by extracting certain values and appending them to lists. For example, the Open_time list is appended with the Open_time value from the data, the volume list is appended with the volume value, and so on. The function also calculates the average of the last six data points and appends the result to the OP list. Finally, the function returns the Open_time, volume, Open, High, Low, and Close lists.

---

這支程式使用了以下套件：  
+ discord：用於與 Discord 交互的庫  
+ numpy：用於數據分析的庫  
+ pybit：用於從 Bybit 檢索加密貨幣數據的庫  
要在你的環境中安裝這些套件，你可以使用 pip 安裝它們。例如，你可以通過執行以下命令來安裝 discord 套件：
```
pip install discord
```
你可以使用類似的命令來安裝 numpy 和 pybit 套件。  
```
pip install numpy
pip install pybit
```
請注意，在執行這些命令之前，你需要確保你已經安裝了 pip。如果你還沒有安裝 pip，你可以通過執行以下命令來安裝它：  
```
python -m ensurepip --upgrade
```

---

本程式被運用於國立臺中科技大學智慧生產工程系二年級人工智慧程式設計之期末報告  
其報告人與開發者名單如下：  
+ 1411068006 吳國維  
+ 1411068014 張健勳  

---

如果您有任何問題歡迎向 CodeRyo 團隊聯繫，您可以透過以下電子郵件發送您的提問或於此 repo 發佈 issue。  
```
hello@coderyo.com
```
