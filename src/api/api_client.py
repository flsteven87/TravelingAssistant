"""
基礎 API 客戶端
"""
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from ..config import API_HEADERS, SYSTEM_CONFIG

class APIError(Exception):
    """API 錯誤"""
    def __init__(self, message: str, status_code: int = None, response: str = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class APIClient:
    """基礎 API 客戶端"""
    
    def __init__(self, base_url: str):
        """
        初始化 API 客戶端
        
        Args:
            base_url: API 基礎 URL
        """
        self.base_url = base_url
        self.headers = API_HEADERS
        self._session = None
        self._session_lock = asyncio.Lock()
    
    async def _get_session(self):
        """獲取或創建 aiohttp ClientSession"""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            return self._session
    
    async def close(self):
        """關閉 aiohttp ClientSession"""
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
                print("API 客戶端會話已關閉")
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        發送 GET 請求
        
        Args:
            endpoint: API 端點
            params: 請求參數
            
        Returns:
            Dict[str, Any]: API 回應
            
        Raises:
            APIError: 如果 API 請求失敗
        """
        url = f"{self.base_url}{endpoint}"
        print(f"GET {url} with params: {params}")
        
        # 重試邏輯
        max_retries = SYSTEM_CONFIG.get("max_retries", 3)
        retry_delay = SYSTEM_CONFIG.get("retry_delay", 1)
        
        for attempt in range(max_retries):
            try:
                session = await self._get_session()
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        print(f"API Error: {response.status} - {error_text}")
                        raise APIError(
                            message=f"API request failed: {error_text}",
                            status_code=response.status,
                            response=error_text
                        )
                    
                    try:
                        response_json = await response.json()
                    except Exception as e:
                        # 如果無法解析 JSON，返回原始文本
                        print(f"無法解析 JSON 回應: {str(e)}")
                        text_response = await response.text()
                        return {"data": text_response}
                    
                    # 如果響應是列表，直接返回
                    if isinstance(response_json, list):
                        return response_json
                    
                    # 如果響應是字典但沒有 data 欄位，添加一個
                    if isinstance(response_json, dict) and "data" not in response_json:
                        # 檢查是否有其他可能的資料欄位
                        for key in ["results", "items", "content"]:
                            if key in response_json:
                                response_json["data"] = response_json[key]
                                break
                    
                    return response_json
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"API 請求錯誤: {str(e)}")
                # 如果發生連接錯誤，關閉並重置會話
                await self.close()
                
                if attempt < max_retries - 1:
                    print(f"重試 ({attempt + 1}/{max_retries})...")
                    await asyncio.sleep(retry_delay)
                else:
                    raise APIError(f"API 連接錯誤: {str(e)}", status_code=500)
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        發送 POST 請求
        
        Args:
            endpoint: API 端點
            data: 請求數據
            
        Returns:
            Dict[str, Any]: API 回應
            
        Raises:
            APIError: 如果 API 請求失敗
        """
        url = f"{self.base_url}{endpoint}"
        print(f"POST {url} with data: {data}")
        
        # 重試邏輯
        max_retries = SYSTEM_CONFIG.get("max_retries", 3)
        retry_delay = SYSTEM_CONFIG.get("retry_delay", 1)
        
        for attempt in range(max_retries):
            try:
                session = await self._get_session()
                async with session.post(url, json=data, headers=self.headers) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        print(f"API Error: {response.status} - {error_text}")
                        raise APIError(
                            message=f"API request failed: {error_text}",
                            status_code=response.status,
                            response=error_text
                        )
                    
                    try:
                        response_json = await response.json()
                    except Exception as e:
                        # 如果無法解析 JSON，返回原始文本
                        print(f"無法解析 JSON 回應: {str(e)}")
                        text_response = await response.text()
                        return {"data": text_response}
                    
                    # 如果響應是列表，直接返回
                    if isinstance(response_json, list):
                        return response_json
                    
                    # 如果響應是字典但沒有 data 欄位，添加一個
                    if isinstance(response_json, dict) and "data" not in response_json:
                        # 檢查是否有其他可能的資料欄位
                        for key in ["results", "items", "content"]:
                            if key in response_json:
                                response_json["data"] = response_json[key]
                                break
                    
                    return response_json
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"API 請求錯誤: {str(e)}")
                # 如果發生連接錯誤，關閉並重置會話
                await self.close()
                
                if attempt < max_retries - 1:
                    print(f"重試 ({attempt + 1}/{max_retries})...")
                    await asyncio.sleep(retry_delay)
                else:
                    raise APIError(f"API 連接錯誤: {str(e)}", status_code=500)
