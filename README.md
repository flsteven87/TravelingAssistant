# 旅館推薦 & 行程規劃 Multi-Agent 系統

這是一個基於 Multi-Agent 架構的旅遊助手系統，包含「旅宿推薦 Agent」和「行程規劃 Agent」，為用戶提供旅遊住宿與周邊探索的整合解決方案。

## 系統特點

- 在 5 秒內回應用戶的初步查詢
- 在 30 秒內提供完整建議
- 協調多個專業 Agent 提供整合服務
- 提供漸進式回應，即使在完整結果尚未準備好時也能提供即時反饋
- 最終輸出包含：推薦住宿選項、周邊景點安排、交通建議

## 目錄結構

```
.
├── app.py                  # Streamlit 應用程序入口
├── requirements.txt        # 依賴項列表
├── .env.example            # 環境變數範例
├── .env                    # 環境變數（不包含在版本控制中）
└── src/                    # 源代碼目錄
    ├── __init__.py
    └── agents/             # Agent 模組
        ├── __init__.py
        ├── base_agent.py   # 基礎 Agent 類別
        └── orchestrator_agent.py  # 協調者 Agent
```

## 安裝與設置

1. 克隆此倉庫：
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. 安裝依賴項：
   ```bash
   pip install -r requirements.txt
   ```

3. 設置環境變數：
   ```bash
   cp .env.example .env
   ```
   然後編輯 `.env` 文件，填入您的 OpenAI API 密鑰和旅遊 API 密鑰。

## 運行應用程序

```bash
streamlit run app.py
```

應用程序將在 http://localhost:8501 啟動。

## 使用方法

1. 在輸入框中輸入您的旅遊需求
2. 助手會在 5 秒內給出初步回應
3. 在 30 秒內提供完整的旅遊建議

示例問題：
- 我想去台北旅遊，有什麼好的住宿推薦？
- 請幫我規劃一個三天兩夜的花蓮行程
- 我和家人想去墾丁，預算 5000 元，有適合的住宿嗎？

## 架構設計

系統基於 Multi-Agent 架構，主要包含以下組件：

1. **基礎 Agent (BaseAgent)**：
   - 所有專業 Agent 的基礎類別
   - 提供工具管理、記憶管理和任務執行等基本功能

2. **協調者 Agent (OrchestratorAgent)**：
   - 負責與用戶對話，理解需求
   - 協調其他專業 Agent 完成任務
   - 提供漸進式回應

3. **專業 Agent**：
   - 旅宿推薦 Agent：負責推薦適合的住宿選項
   - 行程規劃 Agent：負責規劃周邊景點和活動

## API 使用

系統使用以下 API：

1. **旅宿基礎參數 API**：獲取縣市、鄉鎮區、旅館類型等參數
2. **旅館資訊 API**：獲取旅館列表、詳情、空房情況等
3. **查詢周邊地標 API**：搜尋周邊景點和地標

## 環境變數

專案使用以下環境變數：

- `OPENAI_API_KEY`: OpenAI API 密鑰，用於生成回應
- `TRAVEL_API_KEY`: 旅遊 API 密鑰，用於獲取旅遊相關數據

## 開發者

- [您的名字]

## 授權

[授權信息]