"""
旅宿相關 API 封裝
"""
from typing import Dict, Any, List, Optional
from .api_client import APIClient
from ..config import API_BASE_URL, HOTEL_API
import asyncio
from datetime import datetime

class HotelAPI:
    """旅宿相關 API 封裝"""
    
    def __init__(self):
        """初始化旅宿 API 客戶端"""
        self.client = APIClient(API_BASE_URL)
    
    async def get_counties(self) -> List[Dict[str, Any]]:
        """
        獲取縣市列表
        
        Returns:
            List[Dict[str, Any]]: 縣市列表
        """
        response = await self.client.get(HOTEL_API["counties"])
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def get_districts(self, county_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        獲取鄉鎮區列表
        
        Args:
            county_id: 縣市 ID
            
        Returns:
            List[Dict[str, Any]]: 鄉鎮區列表
        """
        params = {}
        if county_id:
            params["county_id"] = county_id
            
        response = await self.client.get(HOTEL_API["districts"], params=params)
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def get_hotel_types(self) -> List[Dict[str, Any]]:
        """
        獲取旅館類型列表
        
        Returns:
            List[Dict[str, Any]]: 旅館類型列表
        """
        response = await self.client.get(HOTEL_API["hotel_types"])
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def get_hotel_facilities(self) -> List[str]:
        """
        獲取飯店設施列表
        
        Returns:
            List[str]: 飯店設施名稱列表
        """
        response = await self.client.get(HOTEL_API["hotel_facilities"])
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            facilities_data = response
        else:
            facilities_data = response.get("data", [])
        
        # 從設施對象中提取名稱
        facilities_names = []
        for facility in facilities_data:
            if isinstance(facility, dict) and "name" in facility:
                facilities_names.append(facility["name"])
            elif isinstance(facility, str):
                facilities_names.append(facility)
        
        return facilities_names
    
    async def get_room_facilities(self) -> List[str]:
        """
        獲取房間備品列表
        
        Returns:
            List[str]: 房間備品名稱列表
        """
        response = await self.client.get(HOTEL_API["room_facilities"])
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            facilities_data = response
        else:
            facilities_data = response.get("data", [])
        
        # 從設施對象中提取名稱
        facilities_names = []
        for facility in facilities_data:
            if isinstance(facility, dict) and "name" in facility:
                facilities_names.append(facility["name"])
            elif isinstance(facility, str):
                facilities_names.append(facility)
        
        return facilities_names
    
    async def get_bed_types(self) -> List[Dict[str, Any]]:
        """
        獲取房間床型列表
        
        Returns:
            List[Dict[str, Any]]: 房間床型列表
        """
        response = await self.client.get(HOTEL_API["bed_types"])
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def get_hotels(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        獲取旅館列表
        
        Args:
            params: 查詢參數
            
        Returns:
            List[Dict[str, Any]]: 旅館列表
        """
        response = await self.client.get(HOTEL_API["hotels"], params=params)
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
            
        data = response.get("data", [])
        
        # 檢查回傳的資料結構
        if isinstance(data, dict) and "hotels" in data:
            # 如果回傳的是 {"hotels": [...]} 格式
            return data["hotels"]
        elif isinstance(data, list):
            # 如果回傳的是 [...] 格式
            return data
        else:
            # 其他情況，返回空列表
            return []
    
    async def fuzzy_match_hotel(self, name: str) -> List[Dict[str, Any]]:
        """
        模糊比對旅館名稱
        
        Args:
            name: 旅館名稱
            
        Returns:
            List[Dict[str, Any]]: 匹配的旅館列表
        """
        params = {"name": name}
        response = await self.client.get(HOTEL_API["hotel_fuzzy_match"], params=params)
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def get_hotel_detail(self, hotel_id: str) -> Dict[str, Any]:
        """
        獲取旅館詳細信息
        
        Args:
            hotel_id: 旅館 ID
            
        Returns:
            Dict[str, Any]: 旅館詳細信息
        """
        # 檢查 API 端點是否正確
        try:
            # 使用 hotels API 獲取特定旅館的詳細信息
            params = {"id": hotel_id}
            response = await self.client.get(HOTEL_API["hotels"], params=params)
            
            # 處理 API 直接回傳列表的情況
            if isinstance(response, list):
                data = response
            else:
                data = response.get("data", [])
            
            # 如果返回的是列表，找到匹配的旅館
            if isinstance(data, list):
                for hotel in data:
                    if str(hotel.get("id", "")) == str(hotel_id):
                        return hotel
            
            # 如果沒有找到匹配的旅館，返回空字典
            return {}
        except Exception as e:
            print(f"獲取旅館詳細信息時發生錯誤: {str(e)}")
            return {}
    
    async def search_hotels_by_supply(self, supply_ids: List[str]) -> List[Dict[str, Any]]:
        """
        根據備品搜尋旅館
        
        Args:
            supply_ids: 備品 ID 列表
            
        Returns:
            List[Dict[str, Any]]: 旅館列表
        """
        # 確保 supply_ids 是字串列表
        if supply_ids and isinstance(supply_ids[0], dict) and "id" in supply_ids[0]:
            supply_ids = [str(item["id"]) for item in supply_ids]
        
        params = {"supply_ids": ",".join(supply_ids)}
        response = await self.client.get(HOTEL_API["hotel_supply"], params=params)
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def get_plans(self, hotel_id: str, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        獲取旅館訂購方案
        
        Args:
            hotel_id: 旅館 ID
            keyword: 關鍵字
            
        Returns:
            List[Dict[str, Any]]: 訂購方案列表
        """
        try:
            # 準備參數
            params = {
                "hotel_id": hotel_id,
                "check_in_start_at": datetime.now().strftime("%Y-%m-%d")  # 使用當前日期作為入住開始日期
            }
            if keyword:
                params["keyword"] = keyword
                
            response = await self.client.get(HOTEL_API["plans"], params=params)
            # 處理 API 直接回傳列表的情況
            if isinstance(response, list):
                return response
            return response.get("data", [])
        except Exception as e:
            print(f"獲取旅館訂購方案時發生錯誤: {str(e)}")
            return []
    
    async def search_vacancies(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        多條件搜尋可訂旅館空房
        
        Args:
            params: 搜尋參數
            
        Returns:
            List[Dict[str, Any]]: 可訂旅館空房列表
        """
        response = await self.client.get(HOTEL_API["vacancies"], params=params)
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
