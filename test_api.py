#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試 API 功能
"""
import asyncio
import sys
from src.api.hotel_api import HotelAPI
from src.api.place_api import PlaceAPI

async def test_hotel_api():
    """測試旅宿 API"""
    print("測試旅宿 API...")
    hotel_api = HotelAPI()
    
    try:
        # 測試獲取縣市列表
        counties = await hotel_api.get_counties()
        print(f"縣市列表: {len(counties)} 筆資料")
        
        # 測試獲取旅館類型列表
        hotel_types = await hotel_api.get_hotel_types()
        print(f"旅館類型列表: {len(hotel_types)} 筆資料")
        
        # 測試獲取飯店設施列表
        hotel_facilities = await hotel_api.get_hotel_facilities()
        print(f"飯店設施列表: {len(hotel_facilities)} 筆資料")
        print(f"設施範例: {hotel_facilities[:3] if hotel_facilities else []}")
        
        # 測試獲取房間備品列表
        room_facilities = await hotel_api.get_room_facilities()
        print(f"房間備品列表: {len(room_facilities)} 筆資料")
        print(f"備品範例: {room_facilities[:3] if room_facilities else []}")
        
        # 測試獲取旅館列表
        hotels = await hotel_api.get_hotels({"limit": 5})
        print(f"旅館列表: {len(hotels)} 筆資料")
        
        # 如果有旅館資料，測試獲取旅館詳細信息
        if hotels:
            hotel_id = hotels[0].get("id")
            if hotel_id:
                hotel_detail = await hotel_api.get_hotel_detail(hotel_id)
                print(f"旅館詳細信息: {hotel_detail.get('name', '未知')}")
                
                # 測試獲取旅館訂購方案
                plans = await hotel_api.get_plans(hotel_id)
                print(f"旅館訂購方案: {len(plans)} 筆資料")
        
        # 關閉 API 客戶端
        await hotel_api.client.close()
        print("旅宿 API 測試完成")
    except Exception as e:
        print(f"旅宿 API 測試失敗: {str(e)}")
        await hotel_api.client.close()

async def test_place_api():
    """測試地點 API"""
    print("測試地點 API...")
    place_api = PlaceAPI()
    
    try:
        # 測試搜尋周邊地點
        places = await place_api.search_nearby_places("餐廳", location="25.0330,121.5654", radius=500)
        print(f"周邊地點: {len(places.get('places', []))} 筆資料")
        
        # 測試獲取周邊地圖
        map_url = await place_api.get_surroundings_map("25.0330,121.5654")
        print(f"周邊地圖 URL: {'有' if map_url else '無'}")
        
        # 關閉 API 客戶端
        await place_api.client.close()
        print("地點 API 測試完成")
    except Exception as e:
        print(f"地點 API 測試失敗: {str(e)}")
        await place_api.client.close()

async def main():
    """主函數"""
    print("開始測試 API 功能...")
    
    # 測試旅宿 API
    await test_hotel_api()
    
    # 測試地點 API
    await test_place_api()
    
    print("API 測試完成")

if __name__ == "__main__":
    asyncio.run(main()) 