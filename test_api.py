#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試 API 功能
"""
import asyncio
import sys
from src.api.hotel_api import HotelAPI
from src.api.place_api import PlaceAPI
import aiohttp
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 載入環境變數
load_dotenv()

async def test_api(endpoint, description, params=None):
    """測試指定的 API 端點"""
    # API 設定
    API_BASE_URL = "https://k6oayrgulgb5sasvwj3tsy7l7u0tikfd.lambda-url.ap-northeast-1.on.aws"
    API_KEY = os.getenv("API_KEY")
    
    # 如果沒有找到 API_KEY，使用預設的外部專用 API Key
    if not API_KEY:
        API_KEY = "DhDkXZkGXaYBZhkk1Z9m9BuZDJGy"
    
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY
    }
    
    url = f"{API_BASE_URL}{endpoint}"
    
    print(f"\n===== 測試 {description} API =====")
    print(f"正在請求 API: {url}")
    print(f"使用的 headers: {headers}")
    if params:
        print(f"使用的參數: {params}")
    
    # 發送請求
    async with aiohttp.ClientSession() as session:
        if params:
            async with session.get(url, headers=headers, params=params) as response:
                return await process_response(response, description)
        else:
            async with session.get(url, headers=headers) as response:
                return await process_response(response, description)

async def test_post_api(endpoint, description, data=None):
    """測試指定的 POST API 端點"""
    # API 設定
    API_BASE_URL = "https://k6oayrgulgb5sasvwj3tsy7l7u0tikfd.lambda-url.ap-northeast-1.on.aws"
    API_KEY = os.getenv("API_KEY")
    
    # 如果沒有找到 API_KEY，使用預設的外部專用 API Key
    if not API_KEY:
        API_KEY = "DhDkXZkGXaYBZhkk1Z9m9BuZDJGy"
    
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE_URL}{endpoint}"
    
    print(f"\n===== 測試 {description} API =====")
    print(f"正在請求 API: {url}")
    print(f"使用的 headers: {headers}")
    if data:
        print(f"使用的數據: {data}")
    
    # 發送請求
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            return await process_response(response, description)

async def process_response(response, description):
    """處理 API 回應"""
    if response.status == 200:
        data = await response.json()
        print("\n=== API 回應 ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 分析資料結構
        print("\n=== 資料結構分析 ===")
        if isinstance(data, list):
            print(f"資料是一個列表，包含 {len(data)} 個項目")
            if data:
                print(f"第一個項目的結構:")
                first_item = data[0]
                for key, value in first_item.items():
                    print(f"  - {key}: {type(value).__name__} 類型，值為 {value}")
        elif isinstance(data, dict):
            if "data" in data:
                if isinstance(data["data"], list):
                    print(f"資料是一個包含列表的字典，列表包含 {len(data['data'])} 個項目")
                    if data["data"]:
                        print(f"第一個項目的結構:")
                        first_item = data["data"][0]
                        for key, value in first_item.items():
                            print(f"  - {key}: {type(value).__name__} 類型，值為 {value}")
                else:
                    print(f"資料是一個字典，'data' 欄位是 {type(data['data']).__name__} 類型")
            else:
                print("資料是一個字典，但沒有 'data' 欄位")
                print("字典的頂層鍵:")
                for key in data.keys():
                    print(f"  - {key}")
        else:
            print(f"資料是一個 {type(data).__name__} 類型")
        
        # 提取資料
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            items = data["data"]
        
        if items:
            print(f"\n=== {description}列表 ===")
            for item in items[:10]:  # 只顯示前10個項目
                if "name" in item:
                    if "id" in item:
                        print(f"ID: {item.get('id', 'N/A')}, 名稱: {item.get('name', 'N/A')}")
                    else:
                        print(f"名稱: {item.get('name', 'N/A')}")
                elif "type" in item and "name" in item:
                    print(f"類型: {item.get('type', 'N/A')}, 名稱: {item.get('name', 'N/A')}")
                else:
                    print(f"項目: {item}")
            
            if len(items) > 10:
                print(f"... 還有 {len(items) - 10} 個項目未顯示")
        
        # 返回數據以供其他測試使用
        return data
    else:
        print(f"錯誤: {response.status}")
        print(await response.text())
        return None

async def main():
    # 創建 API 客戶端
    hotel_api = HotelAPI()
    place_api = PlaceAPI()
    
    print("開始測試所有 API...")
    
    # 1. 測試飯店類型 API
    await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotel_group/types", "飯店類型")
    
    """
    # 飯店類型 API 回傳資料範例
    [
      {
        "type": "HOTEL",
        "name": "飯店"
      },
      {
        "type": "HOSTEL",
        "name": "青年旅館"
      },
      {
        "type": "HOMESTAY",
        "name": "民宿"
      }
    ]
    """
    
    # 2. 測試縣市 API
    counties_data = await test_api("/api/v3/tools/interview_test/taiwan_hotels/counties", "縣市")
    
    """
    # 縣市 API 回傳資料範例
    [
      {
        "id": "63000",
        "name": "臺北市"
      },
      {
        "id": "65000",
        "name": "新北市"
      },
      {
        "id": "68000",
        "name": "桃園市"
      }
    ]
    """
    
    # 3. 測試鄉鎮區 API (不帶參數)
    await test_api("/api/v3/tools/interview_test/taiwan_hotels/districts", "所有鄉鎮區")
    
    """
    # 鄉鎮區 API (不帶參數) 回傳資料範例
    [
      {
        "id": "63001",
        "county_id": "63000",
        "name": "松山區"
      },
      {
        "id": "63002",
        "county_id": "63000",
        "name": "信義區"
      },
      {
        "id": "63003",
        "county_id": "63000",
        "name": "大安區"
      }
    ]
    """
    
    # 4. 測試鄉鎮區 API (帶縣市參數)
    if counties_data:
        # 提取第一個縣市的 ID
        county_id = None
        if isinstance(counties_data, list) and counties_data:
            county_id = counties_data[0].get("id")
        elif isinstance(counties_data, dict) and "data" in counties_data and counties_data["data"]:
            county_id = counties_data["data"][0].get("id")
        
        if county_id:
            await test_api("/api/v3/tools/interview_test/taiwan_hotels/districts", f"特定縣市({county_id})的鄉鎮區", {"county_id": county_id})
    
    """
    # 鄉鎮區 API (帶縣市參數) 回傳資料範例
    [
      {
        "id": "63001",
        "county_id": "63000",
        "name": "松山區"
      },
      {
        "id": "63002",
        "county_id": "63000",
        "name": "信義區"
      },
      {
        "id": "63003",
        "county_id": "63000",
        "name": "大安區"
      }
    ]
    """
    
    # 5. 測試飯店設施 API
    await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotel/facilities", "飯店設施")
    
    """
    # 飯店設施 API 回傳資料範例
    [
      {
        "id": 1,
        "name": "24小時接待入住",
        "is_popular": true
      },
      {
        "id": 2,
        "name": "24小時保全",
        "is_popular": false
      },
      {
        "id": 3,
        "name": "24小時櫃檯服務",
        "is_popular": false
      }
    ]
    """
    
    # 6. 測試房間備品 API
    room_facilities_data = await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotel/room_type/facilities", "房間備品")
    
    """
    # 房間備品 API 回傳資料範例
    [
      {
        "id": 1,
        "name": "大毛巾",
        "is_popular": false
      },
      {
        "id": 2,
        "name": "小毛巾",
        "is_popular": false
      },
      {
        "id": 3,
        "name": "牙刷牙膏",
        "is_popular": false
      }
    ]
    """
    
    # 7. 測試房間床型 API
    await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotel/room_type/bed_types", "房間床型")
    
    """
    # 房間床型 API 回傳資料範例
    [
      {
        "id": 1,
        "name": "一大床",
        "description": "一張雙人床"
      },
      {
        "id": 2,
        "name": "兩小床",
        "description": "兩張單人床"
      },
      {
        "id": 3,
        "name": "大及小床",
        "description": "一張雙人床及一張單人床"
      }
    ]
    """
    
    # 8. 測試旅館列表 API (基本參數)
    hotels_data = await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotels", "旅館列表", {"page": 1, "per_page": 10})
    
    """
    # 旅館列表 API 回傳資料範例
    [
      {
        "id": 25,
        "status": "OPEN",
        "domain": "checkinnselecttng",
        "name": "雀客藏居台北南港",
        "phone": "0226 512 251",
        "meals": null,
        "url": "https://www.mastripms.com/checkinnselecttng/view",
        "check_in": "15:00:00",
        "last_check_in": "23:59:00",
        "check_out": "11:00:00",
        "service_mail": "reservation.service@dunqian.com",
        "child_age": 12,
        "address": "115台北市南港區重陽路59號 No. 59, Chongyang Road, Nangang District, Taipei City 115, Taiwan (R.O.C.)",
        "latitude": 25.05591,
        "longitude": 121.59671,
        "intro": "旅行的重頭戲在於找到一個舒適的夜間休息環境，雀客藏居台北南港不僅有完善的住宿需求供應，更強調美感與品味兼具。",
        "cancel_policies": [...],
        "notice": "【一般旅館適用】...",
        "cancel_notice": "【一般旅館適用】...",
        "booking_notice": "【一般旅館適用】...",
        "country": {"name": "臺灣"},
        "province": {"name": "台灣省"},
        "county": {"name": "臺北市"},
        "district": {"name": "南港區"},
        "facilities": [...],
        "images": [...]
      }
    ]
    """
    
    # 9. 測試旅館模糊比對 API
    hotel_name = None
    if hotels_data:
        # 提取第一個旅館的名稱
        if isinstance(hotels_data, list) and hotels_data:
            hotel_name = hotels_data[0].get("name")
        elif isinstance(hotels_data, dict) and "data" in hotels_data and hotels_data["data"]:
            if isinstance(hotels_data["data"], list) and hotels_data["data"]:
                hotel_name = hotels_data["data"][0].get("name")
            elif isinstance(hotels_data["data"], dict) and "hotels" in hotels_data["data"]:
                hotel_name = hotels_data["data"]["hotels"][0].get("name")
    
    if hotel_name:
        # 只取名稱的前幾個字進行模糊比對
        search_term = hotel_name[:3] if len(hotel_name) > 3 else hotel_name
        await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotel/fuzzy_match", "旅館模糊比對", {"hotel_name": search_term})
    else:
        # 使用一個常見的旅館名稱進行測試
        await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotel/fuzzy_match", "旅館模糊比對", {"hotel_name": "福容"})
    
    """
    # 旅館模糊比對 API 回傳資料範例
    [
      {
        "id": 25,
        "name": "雀客藏居台北南港",
        "address": "115台北市南港區重陽路59號 No. 59, Chongyang Road, Nangang District, Taipei City 115, Taiwan (R.O.C.)",
        "latitude": 25.05591,
        "longitude": 121.59671
      },
      {
        "id": 44,
        "name": "雀客藏居台北陽明山",
        "address": "11143台北市士林區菁山路101巷68號",
        "latitude": 25.13889,
        "longitude": 121.54639
      }
    ]
    """
    
    # 10. 測試旅館詳細信息 API
    hotel_id = None
    if hotels_data:
        # 提取第一個旅館的 ID
        if isinstance(hotels_data, list) and hotels_data:
            hotel_id = hotels_data[0].get("id")
        elif isinstance(hotels_data, dict) and "data" in hotels_data and hotels_data["data"]:
            if isinstance(hotels_data["data"], list) and hotels_data["data"]:
                hotel_id = hotels_data["data"][0].get("id")
            elif isinstance(hotels_data["data"], dict) and "hotels" in hotels_data["data"]:
                hotel_id = hotels_data["data"]["hotels"][0].get("id")
    
    if hotel_id:
        await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotels", "旅館詳細信息", {"id": hotel_id})
    
    """
    # 旅館詳細信息 API 回傳資料範例
    [
      {
        "id": 25,
        "status": "OPEN",
        "domain": "checkinnselecttng",
        "name": "雀客藏居台北南港",
        "phone": "0226 512 251",
        "meals": null,
        "url": "https://www.mastripms.com/checkinnselecttng/view",
        "check_in": "15:00:00",
        "last_check_in": "23:59:00",
        "check_out": "11:00:00",
        "service_mail": "reservation.service@dunqian.com",
        "child_age": 12,
        "address": "115台北市南港區重陽路59號 No. 59, Chongyang Road, Nangang District, Taipei City 115, Taiwan (R.O.C.)",
        "latitude": 25.05591,
        "longitude": 121.59671,
        "intro": "旅行的重頭戲在於找到一個舒適的夜間休息環境，雀客藏居台北南港不僅有完善的住宿需求供應，更強調美感與品味兼具。",
        "cancel_policies": [...],
        "notice": "【一般旅館適用】...",
        "cancel_notice": "【一般旅館適用】...",
        "booking_notice": "【一般旅館適用】...",
        "country": {"name": "臺灣"},
        "province": {"name": "台灣省"},
        "county": {"name": "臺北市"},
        "district": {"name": "南港區"},
        "facilities": [...],
        "images": [...],
        "suitable_room_types": [...]
      }
    ]
    """
    
    # 11. 測試根據備品搜尋旅館 API
    # 先獲取房間備品列表
    if room_facilities_data:
        # 提取前兩個備品的 ID
        supply_ids = []
        if isinstance(room_facilities_data, list) and room_facilities_data:
            supply_ids = [str(item.get("id")) for item in room_facilities_data[:2] if "id" in item]
        elif isinstance(room_facilities_data, dict) and "data" in room_facilities_data and room_facilities_data["data"]:
            supply_ids = [str(item.get("id")) for item in room_facilities_data["data"][:2] if "id" in item]
        
        if supply_ids:
            await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotel/supply", "根據備品搜尋旅館", {"supply_ids": ",".join(supply_ids)})
    
    """
    # 根據備品搜尋旅館 API 回傳資料範例
    [
      {
        "id": 25,
        "name": "雀客藏居台北南港",
        "address": "115台北市南港區重陽路59號 No. 59, Chongyang Road, Nangang District, Taipei City 115, Taiwan (R.O.C.)",
        "latitude": 25.05591,
        "longitude": 121.59671
      },
      {
        "id": 44,
        "name": "雀客藏居台北陽明山",
        "address": "11143台北市士林區菁山路101巷68號",
        "latitude": 25.13889,
        "longitude": 121.54639
      }
    ]
    """
    
    # 12. 測試旅館訂購方案 API
    if hotel_id:
        await test_api("/api/v3/tools/interview_test/taiwan_hotels/plans", "旅館訂購方案", {
            "hotel_id": hotel_id,
            "check_in_start_at": datetime.now().strftime("%Y-%m-%d")
        })
    
    """
    # 旅館訂購方案 API 回傳資料範例
    [
      {
        "id": 1423,
        "hotel_id": 8,
        "quota": null,
        "code": "1179",
        "name": "長住20晚方案",
        "type": 3,
        "pricing_type": 2,
        "adjustment_percent": 70,
        "adjustment_money": 1,
        "fixed_money": null,
        "meals": [1],
        "keywords": ["早餐"],
        "cancel_policies": [...],
        "booking_start_at": "2025-01-01 00:00:00",
        "booking_end_at": "2025-10-12 00:00:00",
        "check_in_start_at": "2025-01-01",
        "check_in_end_at": "2025-05-02",
        "unusable_check_in_days_of_week": [],
        "intro": "長住20晚方案",
        "additional_information": null
      },
      {
        "id": 1424,
        "hotel_id": 8,
        "quota": null,
        "code": "1180",
        "name": "長住五天方案",
        "type": 3,
        "pricing_type": 2,
        "adjustment_percent": 85,
        "adjustment_money": 3,
        "fixed_money": null,
        "meals": [1],
        "keywords": ["早餐"],
        "cancel_policies": [...],
        "booking_start_at": "2025-01-01 00:00:00",
        "booking_end_at": "2025-10-23 00:00:00",
        "check_in_start_at": "2025-01-01",
        "check_in_end_at": "2025-05-29",
        "unusable_check_in_days_of_week": [],
        "intro": "長住五天方案",
        "additional_information": null
      }
    ]
    """
    
    # 13. 測試多條件搜尋可訂旅館空房 API
    # 準備搜尋參數
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after_tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    vacancy_params = {
        "check_in_at": tomorrow,
        "check_out_at": day_after_tomorrow,
        "adult_count": 2,
        "child_count": 0
    }
    
    # 如果有縣市 ID，添加到參數中
    if counties_data:
        if isinstance(counties_data, list) and counties_data:
            county_id = counties_data[0].get("id")
        elif isinstance(counties_data, dict) and "data" in counties_data and counties_data["data"]:
            county_id = counties_data["data"][0].get("id")
        
        if county_id:
            vacancy_params["county_id"] = county_id
    
    await test_api("/api/v3/tools/interview_test/taiwan_hotels/hotel/vacancies", "多條件搜尋可訂旅館空房", vacancy_params)
    
    """
    # 多條件搜尋可訂旅館空房 API 回傳資料範例
    [
      {
        "id": 25,
        "name": "雀客藏居台北南港",
        "address": "115台北市南港區重陽路59號 No. 59, Chongyang Road, Nangang District, Taipei City 115, Taiwan (R.O.C.)",
        "latitude": 25.05591,
        "longitude": 121.59671,
        "suitable_room_types": [
          {
            "id": 222,
            "name": "標準雙人客房(天井窗) SD",
            "price": 11000,
            "avg_square_feet": 9,
            "bed_type": "一大床",
            "adults": 2,
            "children": 0,
            "intro": "此房型格局為對內天井窗型(不可開)\r\n房型格局會依照房間位置及房內擺設略有差異，依照入住房況安排。",
            "prices": [
              {
                "booking_plan_id": null,
                "price": 2800,
                "rooms": 7,
                "date": "2025-03-09",
                "plan": {
                  "name": "基本方案",
                  "keywords": []
                }
              }
            ],
            "facilities": [...],
            "plans": []
          }
        ],
        "plans": []
      }
    ]
    """
    
    # 14. 測試周邊地點搜尋 API
    # 使用台北 101 的坐標作為測試
    taipei_101_location = "25.0339639,121.5644722"
    await test_post_api("/api/v3/tools/external/gcp/places/nearby_search_with_query", "周邊地點搜尋", {
        "text_query": "餐廳",
        "location": taipei_101_location,
        "radius": 1000
    })
    
    """
    # 周邊地點搜尋 API 回傳資料範例
    {
      "surroundings_map_images": [
        "https://raccoonai-public-assets.s3.ap-northeast-1.amazonaws.com/farglory/online_chat_images/roadmap_600x600_241e347d0917a0036d1af8465737e0df.png"
      ],
      "places": [
        {
          "types": [
            "japanese_restaurant",
            "restaurant",
            "point_of_interest",
            "food",
            "establishment"
          ],
          "formattedAddress": "日本〒160-0022 Tokyo, Shinjuku City, Shinjuku, 3-chōme−32−１ モトビル B1F",
          "location": {
            "latitude": 35.6899806,
            "longitude": 139.7038098
          },
          "rating": 4.5,
          "displayName": {
            "text": "炸牛排 もと村"
          },
          "currentOpeningHours": {
            "weekdayDescriptions": [
              "星期一: 11:00 – 22:00",
              "星期二: 11:00 – 22:00",
              "星期三: 11:00 – 22:00",
              "星期四: 11:00 – 22:00",
              "星期五: 11:00 – 22:00",
              "星期六: 11:00 – 22:00",
              "星期日: 11:00 – 22:00"
            ]
          }
        }
      ]
    }
    """
    
    print("\n所有 API 測試完成！")

if __name__ == "__main__":
    asyncio.run(main()) 