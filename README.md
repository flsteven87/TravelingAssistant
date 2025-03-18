# 旅館推薦 & 行程規劃 Multi-Agent 系統

本專案是一個基於 Autogen 的多 Agent 系統，專門用於為用戶提供旅遊住宿與周邊探索的整合解決方案。系統包含多個專業 Agent，能夠根據用戶需求推薦適合的旅館、規劃行程，並在短時間內提供反饋。

## 功能特點

- **快速回應**：在 5 秒內提供初步回應，30 秒內提供完整建議
- **多 Agent 協作**：包含旅宿推薦 Agent 和行程規劃 Agent，由協調 Agent 統籌管理
- **漸進式回應**：即使完整結果尚未準備好，也能提供即時反饋
- **完整旅遊規劃**：提供旅館推薦、周邊景點安排和交通建議
- **錯誤處理**：處理各 Agent 回應時間不一致的情況，確保系統穩定性

## 架構設計

系統架構如下：

```
TravelingAssistant/
├── config/            # 配置文件
├── agents/            # Agent 定義
│   ├── user_proxy.py      # 用戶代理
│   ├── hotel_agent.py     # 旅宿推薦代理
│   ├── itinerary_agent.py # 行程規劃代理
│   └── coordinator_agent.py # 協調代理
├── data/              # 模擬數據
│   ├── mock_hotels.py     # 旅館數據
│   └── mock_attractions.py # 景點數據
├── utils/             # 工具函數
│   └── async_helper.py    # 非同步處理工具
├── app.py             # Streamlit 應用程序
└── README.md          # 專案說明
```

### Agent 職責

- **用戶代理 (User Proxy Agent)**：處理用戶輸入，顯示系統回應，管理用戶體驗
- **旅宿推薦代理 (Hotel Recommendation Agent)**：基於用戶偏好推薦最適合的住宿
- **行程規劃代理 (Itinerary Planning Agent)**：根據用戶興趣和住宿位置推薦景點和活動
- **協調代理 (Coordinator Agent)**：協調各專業 Agent，確保及時回應和一致性，負責格式化返回結果

## 通信機制

系統使用 Autogen 框架實現 Agent 之間的通信。主要流程如下：

1. 用戶輸入旅遊需求
2. 協調代理提取需求信息並分發給專業 Agent
3. 專業 Agent 並行處理請求，協調代理管理超時和任務優先級
4. 協調代理收集初步結果並快速回應用戶
5. 專業 Agent 繼續處理完整結果
6. 協調代理整合所有結果，提供完整建議

## 響應格式化

- **協調代理**負責所有響應的格式化，確保一致的用戶體驗
- **漸進式響應**：提供初始、部分和完整三種響應類型，隨著信息收集逐步豐富內容
- **結構化展示**：清晰分類展示旅宿、景點和交通建議，使用 Markdown 增強可讀性

## 資源調度策略

- **任務優先級**：重要任務優先執行，確保關鍵信息優先呈現
- **超時處理**：為每個操作設置超時，超時後返回部分結果而非失敗
- **漸進式呈現**：先提供初步信息，再補充完整細節
- **非同步處理**：使用 Python 的 asyncio 實現非阻塞操作

## 安裝與使用

### 前置需求

- Python 3.8+
- Streamlit
- Autogen 庫

### 安裝

```bash
# 克隆儲存庫
git clone https://github.com/yourusername/TravelingAssistant.git
cd TravelingAssistant

# 安裝依賴
pip install -r requirements.txt
```

### 運行

```bash
streamlit run app.py
```

輸入您的旅遊需求，例如：
```
我想明天帶家人去台北旅遊2天，預算5000元，喜歡歷史和美食。
```

系統將快速回應並提供旅遊建議。

## 擴展和未來發展

- 整合真實 API 獲取最新旅館和景點數據
- 添加更多類型的專業 Agent，如餐廳推薦、天氣預報等
- 改進自然語言處理能力，提取更精確的用戶需求
- 實現用戶反饋循環，根據用戶對建議的評價持續優化

## 貢獻

歡迎提交 Pull Request 或開 Issue 討論您的想法和建議。

## 授權

本專案採用 MIT 授權 - 詳見 LICENSE 文件 