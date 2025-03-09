#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試 HotelAgent 的 get_hotel_detail 功能
"""
import asyncio
import sys
from src.agents.hotel_agent import HotelAgent, HotelDetailQuery, HotelQuery
import json
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

async def test_get_hotel_detail():
    """測試 HotelAgent 的 get_hotel_detail 功能"""
    print("開始測試 HotelAgent 的 get_hotel_detail 功能...")
    
    # 創建 HotelAgent 實例
    agent = HotelAgent(verbose=True)
    
    try:
        # 測試獲取旅館列表
        print("\n===== 測試獲取旅館列表 =====")
        hotels = await agent.get_hotels(HotelQuery(page=1, per_page=5))
        
        if not hotels:
            print("獲取旅館列表失敗，無法繼續測試")
            return
        
        # 獲取第一個旅館的 ID
        hotel_id = str(hotels[0]["id"])
        print(f"獲取到旅館 ID: {hotel_id}")
        
        # 測試獲取旅館詳細信息
        print("\n===== 測試獲取旅館詳細信息 =====")
        hotel_detail = await agent.get_hotel_detail(HotelDetailQuery(id=hotel_id))
        
        if hotel_detail:
            print("\n=== 旅館詳細信息 ===")
            print(f"名稱: {hotel_detail.get('name', '未知')}")
            print(f"地址: {hotel_detail.get('address', '未知')}")
            print(f"入住時間: {hotel_detail.get('check_in', '未知')}")
            print(f"退房時間: {hotel_detail.get('check_out', '未知')}")
            print(f"簡介: {hotel_detail.get('intro', '無簡介')[:100]}...")
            
            # 顯示設施
            facilities = hotel_detail.get("facilities", [])
            if facilities:
                print("\n=== 設施 ===")
                for i, facility in enumerate(facilities[:10], 1):
                    if isinstance(facility, dict) and "name" in facility:
                        print(f"{i}. {facility['name']}")
                    elif isinstance(facility, str):
                        print(f"{i}. {facility}")
                
                if len(facilities) > 10:
                    print(f"...還有 {len(facilities) - 10} 個設施未顯示")
            
            # 顯示房型
            room_types = hotel_detail.get("suitable_room_types", [])
            if room_types:
                print("\n=== 房型 ===")
                for i, room in enumerate(room_types[:5], 1):
                    room_name = room.get("name", "未知房型")
                    room_price = room.get("price", "價格未知")
                    room_bed = room.get("bed_type", "床型未知")
                    print(f"{i}. {room_name} - 價格: {room_price}, 床型: {room_bed}")
                
                if len(room_types) > 5:
                    print(f"...還有 {len(room_types) - 5} 個房型未顯示")
        else:
            print("獲取旅館詳細信息失敗")
        
        print("\n測試完成！")
    finally:
        # 確保關閉 API 客戶端
        if agent.hotel_api and agent.hotel_api.client:
            await agent.hotel_api.client.close()
            print("已關閉 API 客戶端")

if __name__ == "__main__":
    asyncio.run(test_get_hotel_detail()) 