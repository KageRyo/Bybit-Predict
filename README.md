# Bybit-Predict
使用 Python 和 Bybit 交易所 API 預測加密貨幣趨勢  
Predict cryptocurrency trends using Python and the Bybit exchange API

---
這段代碼定義了一個名為 KLineStatus 的函數，它從 Bybit API 檢索和處理加密貨幣數據。該函數接受兩個參數：times 和 Name。times 是指定要檢索哪些數據的時間參數，Name 是指定要檢索數據的加密貨幣對的字符串。

函數首先使用 usdt_perpetual.HTTP 函數初始化與 Bybit API 的未經身份驗證的 HTTP 會話，並將 Bybit API 端點 URL、API 密鑰和 API 秘密作為參數傳遞。然後，它調用此會話上的 query_kline 方法來請求指定的加密貨幣對的 K 線數據。interval 參數設置為 240，對應於 4 小時的時間間隔，limit 參數設置為 1，僅檢索一個數據點。from_time 參數設置為 times 參數的值，該值指定要檢索數據的時間。

函數通過提取某些值並將它們附加到列表中來處理檢索的數據。例如，Open_time 列表會被附加數據中的 Open_time 值，volume 列表會被附加 volume 值，以此類推。函數還計算最後六個數據點的平均值，並將結果附加到 OP 列表中。最後，函數返回 Open_time、volume、Open、High、Low 和 Close 列表。

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

This program is used for the second-year artificial intelligence programming design final report of the Department of Intelligent Production Engineering at National Taichung University of Science and Technology. The list of report presenters and developers is as follows:  
+ 1411068006 Wu,Kuo-Wei
+ 1411068014 Chang,Chien-Hsun
 
---

如果您有任何問題歡迎向 CodeRyo 團隊聯繫，您可以透過以下電子郵件發送您的提問或於此 repo 發佈 issue。  
If you have any questions, please don't hesitate to contact the CodeRyo team. You can send your questions via email or create an issue in this repo.  
```
hello@coderyo.com
```

---

歡迎大家對本項目進行貢獻！如果你想發送一個 pull request，請先 fork 本項目並在本地做出你的修改。然後，在你的 fork 上發送一個 pull request，我們會審核你的修改並考慮合併到主分支。感謝你的貢獻！  
Welcome to contribute to this project! If you want to send a pull request, please first fork the project and make your changes locally. Then, send a pull request on your fork, and we will review your changes and consider merging them into the master branch. Thank you for your contribution!  
