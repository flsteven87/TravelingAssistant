# 2025 JTCG AI Engineer Coding Test V3

## 程式實作題

### 提交時限：面試前 24hr 提交

提交細節：

1. 請將以下實作內容開 Github Repository 存放。
2. 請盡量透過開新 branch, 寫 commit message, 發 merge request, 合併分支等，讓驗收人員了解您的開發過程。
3. 請將您的實作內容文件在 README.md。

---

# 旅館推薦 & 行程規劃 Multi-Agent 設計

## 題目描述

設計一個 Multi-Agent 系統，包含「旅宿推薦 Agent」和「行程規劃 Agent」，為用戶提供旅遊住宿與周邊探索的整合解決方案。

**系統需要在 5 秒內回應用戶的初步查詢，並在30秒內提供完整建議。**

### 關鍵需求

- 依據 API 參數，要求用戶提供推薦旅宿所需資訊，例如: 目的地、旅遊日期、人數、預算等
- 系統需協調兩個專業 Agent：旅宿推薦和行程規劃
- 即使在完整結果尚未準備好時，也要提供即時反饋
- 最終輸出需包含：推薦住宿選項、周邊景點安排、交通建議
- 系統必須處理各Agent回應時間不一致的情況

## 技術需求

- 設計Agent間的通信和協調機制
- 處理資源競爭和並行處理
- 實現漸進式回應策略
- 確保系統穩定性和容錯機制
- 考慮用戶互動和反饋循環

## API 列表

API Doc: https://raccoonai-agents-api.readme.io/reference/tools_v3__taiwanhotels_get_countries_api_v3_tools_interview_test_taiwan_hotels_countries_get

- 外部專用 API Key: `Authorization: DhDkXZkGXaYBZhkk1Z9m9BuZDJGy`

1. **旅宿基礎參數API**
    - `GET /api/v3/tools/interview_test/taiwan_hotels/counties`  - [取得縣市參數](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_counties_api_v3_tools_interview_test_taiwan_hotels_counties_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/districts` - [取得鄉鎮區參數](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_districts_api_v3_tools_interview_test_taiwan_hotels_districts_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/hotel_group/types` - [取得旅館類型參數](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_hotel_group_types_api_v3_tools_interview_test_taiwan_hotels_hotel_group_types_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/hotel/facilities`  -  [取得飯店設施參數](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_hotel_facilities_api_v3_tools_interview_test_taiwan_hotels_hotel_facilities_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/hotel/room_type/facilities` - [取得房間備品參數](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_hotel_room_type_facilities_api_v3_tools_interview_test_taiwan_hotels_hotel_room_type_facilities_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/hotel/room_type/bed_types` - [取得房間床型參數](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_hotel_room_type_bed_types_api_v3_tools_interview_test_taiwan_hotels_hotel_room_type_bed_types_get)
2. **旅館資訊API**
    - `GET /api/v3/tools/interview_test/taiwan_hotels/hotels`  - [取得指定類別旅館](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_hotels_api_v3_tools_interview_test_taiwan_hotels_hotels_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/hotel/fuzzy_match`  - [模糊比對旅館名稱](https://raccoonai-agents-api.readme.io/reference/tools_v3__taiwanhotels_guess_hotel_api_v3_tools_interview_test_taiwan_hotels_hotel_fuzzy_match_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/hotel/detail`  - [指定 id 查詢旅館介紹](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_hotel_details_api_v3_tools_interview_test_taiwan_hotels_hotel_details_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/hotel/supply`  - [根據備品搜尋旅館](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_hotel_supply_api_v3_tools_interview_test_taiwan_hotels_hotel_supply_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/plans`  - [根據關鍵字及旅館 id 搜尋可用訂購方案](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_plans_api_v3_tools_interview_test_taiwan_hotels_plans_get)
    - `GET /api/v3/tools/interview_test/taiwan_hotels/hotel/vacancies`  - [多條件搜尋可訂旅館空房](https://raccoonai-agents-api.readme.io/reference/tools_v3__dunqian_get_hotel_room_vacancies_api_v3_tools_interview_test_taiwan_hotels_hotel_vacancies_get)
3. **查詢周邊地標 API**
    - `GET /api/v3/tools/external/gcp/places/nearby_search_with_query`  - [搜尋周邊地標](https://raccoonai-agents-api.readme.io/reference/tools_v3__external_gcp_places_nearby_search_with_query_api_v3_tools_external_gcp_places_nearby_search_with_query_post)
        - 參數：text_query
            - ex: 雀客信義附近的捷運站
        - 回應：靜態周邊地圖圖像、地點資訊列表
            
            ```json
            {
                "surroundings_map_images": [
                    "https://raccoonai-public-assets.s3.ap-northeast-1.amazonaws.com/farglory/online_chat_images/roadmap_600x600_5029092ed7a367d345e826f9427fd0ac.png"
                ],
                "places": [
                    {
                        "types": [
                            "hotel",
                            "inn",
                            "lodging",
                            "point_of_interest",
                            "establishment"
                        ],
                        "formattedAddress": "10057台北市中正區信義路二段73號",
                        "location": {
                            "latitude": 25.0346126,
                            "longitude": 121.5265462
                        },
                        "rating": 4.7,
                        "displayName": {
                            "text": "雀客快捷 - 台北永康"
                        }
                    }
                ]
            }
            ```
            

## 評分標準

1. **架構設計 (40%)**
    - Agent職責劃分的合理性
    - 通信機制的效率
    - 資源調度策略
    - 可擴展性考量
2. **響應策略 (30%)**
    - 初步快速回應的實現
    - 漸進式結果展示
    - 處理延遲和超時
    - 優先級設定機制
3. **用戶體驗 (20%)**
    - 交互設計的自然流暢度
    - 反饋機制的設計
    - 結果呈現的清晰度
    - 例外情況的處理
4. **實用性與創新 (10%)**
    - 是否考慮到實際場景的限制
    - 有無獨特的創新設計
    - 系統的易用性和易實現性

## 提交項目

1. 多 Agent 系統程式碼
2. Agent 架構說明
3. 用戶問答測試結果