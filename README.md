# TravelingAssistant

一個 Python 旅行助手應用，幫助用戶規劃行程、管理預算、提供旅行建議和當地資訊。

## 功能特色

- 🗺️ **行程規劃**：根據目的地、時間和預算自動生成行程建議
- 💰 **預算管理**：追蹤和管理旅行預算，記錄支出
- 🏨 **住宿推薦**：根據位置和預算提供住宿選項
- 🍽️ **餐廳發現**：推薦當地特色餐廳和美食
- 🚗 **交通指南**：提供目的地交通資訊和選項
- 🌦️ **天氣預報**：即時天氣資訊和預報
- 📝 **旅行筆記**：記錄旅行體驗和回憶
- 📱 **離線功能**：支援離線使用基本功能

## 安裝

```bash
# 克隆儲存庫
git clone https://github.com/flsteven87/TravelingAssistant.git
cd TravelingAssistant

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

## 使用方法

```bash
# 啟動應用
python src/main.py
```

## 專案結構

```
TravelingAssistant/
├── src/                  # 源代碼
│   ├── main.py           # 主程序入口
│   ├── api/              # API 連接模組
│   ├── models/           # 數據模型
│   ├── utils/            # 工具函數
│   └── ui/               # 用戶界面
├── tests/                # 測試文件
├── data/                 # 數據文件
├── docs/                 # 文檔
├── requirements.txt      # 依賴列表
└── README.md             # 專案說明
```

## 貢獻

歡迎提交 Pull Request 或開 Issue 來改進專案。

## 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件。