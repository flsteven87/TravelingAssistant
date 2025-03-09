"""
地點相關 API 封裝
"""
from typing import Dict, Any, List, Optional
from .api_client import APIClient
from ..config import API_BASE_URL, PLACE_API

class PlaceAPI:
    """地點相關 API 封裝"""
    
    def __init__(self):
        """初始化地點 API 客戶端"""
        self.client = APIClient(API_BASE_URL)
    
    async def search_nearby_places(self, query: str, location: Optional[str] = None, radius: int = 1000) -> Dict[str, Any]:
        """
        搜尋周邊地點
        
        Args:
            query: 搜尋關鍵字
            location: 位置坐標 (經緯度)，格式為 "latitude,longitude"
            radius: 搜尋半徑 (米)
            
        Returns:
            Dict[str, Any]: 搜尋結果，包含地圖圖像和地點列表
        """
        data = {
            "text_query": query,
            "radius": radius
        }
        
        if location:
            data["location"] = location
        
        try:
            response = await self.client.post(PLACE_API["nearby_search"], data=data)
            
            # 確保回傳的資料格式正確
            surroundings_map_images = response.get("surroundings_map_images", [])
            places = response.get("places", [])
            
            # 如果 places 是字典列表，確保每個字典都有必要的欄位
            if places and isinstance(places[0], dict):
                for place in places:
                    # 確保每個地點都有名稱
                    if "name" not in place:
                        place["name"] = "未知地點"
                    # 確保每個地點都有地址
                    if "address" not in place:
                        place["address"] = "未知地址"
            
            return {
                "surroundings_map_images": surroundings_map_images,
                "places": places
            }
        except Exception as e:
            print(f"搜尋周邊地點時發生錯誤: {str(e)}")
            return {
                "surroundings_map_images": [],
                "places": []
            }
    
    async def get_surroundings_map(self, location: str) -> str:
        """
        獲取周邊地圖圖像
        
        Args:
            location: 位置坐標 (經緯度)，格式為 "latitude,longitude"
            
        Returns:
            str: 地圖圖像 URL
        """
        try:
            # 使用空查詢獲取地圖
            result = await self.search_nearby_places("", location=location)
            map_images = result.get("surroundings_map_images", [])
            
            # 返回第一張地圖圖像，如果沒有則返回空字符串
            return map_images[0] if map_images else ""
        except Exception as e:
            print(f"獲取周邊地圖時發生錯誤: {str(e)}")
            return ""
