"""
旅宿相關 API 封裝
"""
from typing import Dict, Any, List, Optional
from .api_client import APIClient
import asyncio
from datetime import datetime

class HotelAPI:
    """旅宿相關 API 封裝"""
    
    def __init__(self):
        """初始化旅宿 API 客戶端"""
        # 硬編碼 API 基礎 URL
        self.client = APIClient("https://api.travel-assistant.example.com")
        # 硬編碼 API 端點
        self.endpoints = {
            "counties": "/hotels/counties",
            "districts": "/hotels/districts",
            "hotel_types": "/hotels/types",
            "hotel_facilities": "/hotels/facilities",
            "room_facilities": "/hotels/room-facilities",
            "bed_types": "/hotels/bed-types",
            "hotels": "/hotels",
            "fuzzy_match": "/hotels/fuzzy-match",
            "hotel_detail": "/hotels/detail",
            "search_by_supply": "/hotels/search-by-supply",
            "plans": "/hotels/plans",
            "vacancies": "/hotels/vacancies"
        }
    
    async def get_counties(self) -> List[Dict[str, Any]]:
        """
        獲取縣市列表
        
        Returns:
            List[Dict[str, Any]]: 縣市列表
        """
        response = await self.client.get(self.endpoints["counties"])
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
            
        response = await self.client.get(self.endpoints["districts"], params=params)
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def get_hotel_types(self) -> List[Dict[str, Any]]:
        """
        獲取旅宿類型列表
        
        Returns:
            List[Dict[str, Any]]: 旅宿類型列表
        """
        response = await self.client.get(self.endpoints["hotel_types"])
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def get_hotel_facilities(self) -> List[str]:
        """
        獲取旅宿設施列表
        
        Returns:
            List[str]: 旅宿設施列表
        """
        response = await self.client.get(self.endpoints["hotel_facilities"])
        
        # 資料標準化:
        # 1. 如果 API 回傳的是字串列表，直接回傳
        if isinstance(response, list) and all(isinstance(item, str) for item in response):
            return response
            
        # 2. 如果回傳的是物件列表，嘗試萃取設施名稱
        if isinstance(response, list) and all(isinstance(item, dict) for item in response):
            try:
                return [item.get("name", "") for item in response if "name" in item]
            except:
                pass
                
        # 3. 如果回傳的是包含資料欄位的物件
        data = None
        if isinstance(response, dict):
            data = response.get("data", None)
            
        # 4. 如果資料是字串列表，直接回傳
        if isinstance(data, list) and all(isinstance(item, str) for item in data):
            return data
            
        # 5. 如果資料是物件列表，嘗試萃取設施名稱
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            try:
                return [item.get("name", "") for item in data if "name" in item]
            except:
                pass
                
        # 6. 回傳空列表作為後備
        return []
    
    async def get_room_facilities(self) -> List[str]:
        """
        獲取房間設施列表
        
        Returns:
            List[str]: 房間設施列表
        """
        response = await self.client.get(self.endpoints["room_facilities"])
        
        # 資料標準化:
        # 1. 如果 API 回傳的是字串列表，直接回傳
        if isinstance(response, list) and all(isinstance(item, str) for item in response):
            return response
            
        # 2. 如果回傳的是物件列表，嘗試萃取設施名稱
        if isinstance(response, list) and all(isinstance(item, dict) for item in response):
            try:
                return [item.get("name", "") for item in response if "name" in item]
            except:
                pass
                
        # 3. 如果回傳的是包含資料欄位的物件
        data = None
        if isinstance(response, dict):
            data = response.get("data", None)
            
        # 4. 如果資料是字串列表，直接回傳
        if isinstance(data, list) and all(isinstance(item, str) for item in data):
            return data
            
        # 5. 如果資料是物件列表，嘗試萃取設施名稱
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            try:
                return [item.get("name", "") for item in data if "name" in item]
            except:
                pass
                
        # 6. 回傳空列表作為後備
        return []
    
    async def get_bed_types(self) -> List[Dict[str, Any]]:
        """
        獲取床型列表
        
        Returns:
            List[Dict[str, Any]]: 床型列表
        """
        response = await self.client.get(self.endpoints["bed_types"])
        # 處理 API 直接回傳列表的情況
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def get_hotels(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        搜尋旅宿
        
        Args:
            params: 搜尋參數
            
        Returns:
            List[Dict[str, Any]]: 旅宿列表
        """
        try:
            response = await self.client.get(self.endpoints["hotels"], params=params)
            # 處理 API 直接回傳列表的情況
            if isinstance(response, list):
                return response
                
            # 如果 API 回傳的是包含資料欄位的物件
            if isinstance(response, dict):
                data = response.get("data", [])
                
                # 如果 data 是一個列表，直接回傳
                if isinstance(data, list):
                    return data
                
                # 如果 data 是一個物件，嘗試找出列表欄位
                if isinstance(data, dict):
                    for key in ["hotels", "items", "results", "list"]:
                        if key in data and isinstance(data[key], list):
                            return data[key]
            
            return []
        except Exception as e:
            print(f"搜尋旅宿時發生錯誤: {str(e)}")
            return []
    
    async def fuzzy_match_hotel(self, name: str) -> List[Dict[str, Any]]:
        """
        模糊匹配旅宿名稱
        
        Args:
            name: 旅宿名稱
            
        Returns:
            List[Dict[str, Any]]: 匹配的旅宿列表
        """
        try:
            response = await self.client.get(self.endpoints["fuzzy_match"], params={"name": name})
            # 處理 API 直接回傳列表的情況
            if isinstance(response, list):
                return response
            return response.get("data", [])
        except Exception as e:
            print(f"模糊匹配旅宿名稱時發生錯誤: {str(e)}")
            return []
    
    async def get_hotel_detail(self, hotel_id: str) -> Dict[str, Any]:
        """
        獲取旅宿詳情
        
        Args:
            hotel_id: 旅宿 ID
            
        Returns:
            Dict[str, Any]: 旅宿詳情
        """
        try:
            params = {"hotel_id": hotel_id}
            response = await self.client.get(self.endpoints["hotel_detail"], params=params)
            
            # 如果 API 回傳的是字典，直接檢查是否有 data 欄位
            if isinstance(response, dict):
                if "data" in response:
                    return response["data"]
                    
                # 如果沒有 data 欄位，檢查常見欄位
                for key in ["hotel", "result", "detail", "info"]:
                    if key in response and isinstance(response[key], dict):
                        return response[key]
                
                # 如果沒有找到標準欄位，則認為整個回應就是旅宿資料
                return response
                
            # 如果 API 回傳的是一個空值，回傳空字典
            return {}
        except Exception as e:
            print(f"獲取旅宿詳情時發生錯誤: {str(e)}")
            return {}
    
    async def search_hotels_by_supply(self, supply_ids: List[str]) -> List[Dict[str, Any]]:
        """
        根據供應商 ID 搜尋旅宿
        
        Args:
            supply_ids: 供應商 ID 列表
            
        Returns:
            List[Dict[str, Any]]: 旅宿列表
        """
        try:
            # 建立請求參數
            params = {"supply_ids": ",".join(supply_ids)}
            
            response = await self.client.get(self.endpoints["search_by_supply"], params=params)
            # 處理 API 直接回傳列表的情況
            if isinstance(response, list):
                return response
            return response.get("data", [])
        except Exception as e:
            print(f"根據供應商 ID 搜尋旅宿時發生錯誤: {str(e)}")
            return []
    
    async def get_plans(self, hotel_id: str, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        獲取旅宿住宿方案
        
        Args:
            hotel_id: 旅宿 ID
            keyword: 搜尋關鍵字 (可選)
            
        Returns:
            List[Dict[str, Any]]: 住宿方案列表
        """
        try:
            # 建立請求參數
            params = {"hotel_id": hotel_id}
            if keyword:
                params["keyword"] = keyword
                
            response = await self.client.get(self.endpoints["plans"], params=params)
            
            # 處理 API 直接回傳列表的情況
            if isinstance(response, list):
                return response
                
            # 如果 API 回傳的是包含資料欄位的物件
            if isinstance(response, dict):
                data = response.get("data", [])
                
                # 如果 data 是一個列表，直接回傳
                if isinstance(data, list):
                    return data
                
                # 如果 data 是一個物件，嘗試找出列表欄位
                if isinstance(data, dict):
                    for key in ["plans", "items", "results", "list"]:
                        if key in data and isinstance(data[key], list):
                            return data[key]
            
            return []
        except Exception as e:
            print(f"獲取旅宿住宿方案時發生錯誤: {str(e)}")
            return []
    
    async def search_vacancies(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        搜尋空房
        
        Args:
            params: 搜尋參數
            
        Returns:
            List[Dict[str, Any]]: 空房列表
        """
        try:
            response = await self.client.get(self.endpoints["vacancies"], params=params)
            
            # 處理 API 直接回傳列表的情況
            if isinstance(response, list):
                return response
                
            # 如果 API 回傳的是包含資料欄位的物件
            if isinstance(response, dict):
                data = response.get("data", [])
                
                # 如果 data 是一個列表，直接回傳
                if isinstance(data, list):
                    return data
                
                # 如果 data 是一個物件，嘗試找出列表欄位
                if isinstance(data, dict):
                    for key in ["vacancies", "rooms", "items", "results", "list"]:
                        if key in data and isinstance(data[key], list):
                            return data[key]
            
            return []
        except Exception as e:
            print(f"搜尋空房時發生錯誤: {str(e)}")
            return []
