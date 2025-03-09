"""
旅宿推薦 Agent，負責處理旅宿相關查詢和推薦
"""
from typing import Dict, List, Any, Optional, Union, Callable
import json
import asyncio
import openai
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from .base_agent import BaseAgent
from ..api.hotel_api import HotelAPI
from ..api.place_api import PlaceAPI

# 定義 Pydantic 模型用於 function calling
class CountyQuery(BaseModel):
    """獲取縣市列表的查詢參數"""
    pass

class DistrictQuery(BaseModel):
    """獲取鄉鎮區列表的查詢參數"""
    county_id: Optional[str] = Field(None, description="縣市 ID")

class HotelTypeQuery(BaseModel):
    """獲取旅館類型列表的查詢參數"""
    pass

class HotelFacilityQuery(BaseModel):
    """獲取飯店設施列表的查詢參數"""
    pass

class RoomFacilityQuery(BaseModel):
    """獲取房間備品列表的查詢參數"""
    pass

class BedTypeQuery(BaseModel):
    """獲取房間床型列表的查詢參數"""
    pass

class HotelQuery(BaseModel):
    """獲取旅館列表的查詢參數"""
    county_id: Optional[str] = Field(None, description="縣市 ID")
    district_id: Optional[str] = Field(None, description="鄉鎮區 ID")
    hotel_name: Optional[str] = Field(None, description="旅館名稱，用於模糊搜尋")
    hotel_type: Optional[List[str]] = Field(None, description="旅館類型 ID 列表")
    min_price: Optional[int] = Field(None, description="最低價格")
    max_price: Optional[int] = Field(None, description="最高價格")
    check_in_date: Optional[str] = Field(None, description="入住日期，格式為 YYYY-MM-DD")
    check_out_date: Optional[str] = Field(None, description="退房日期，格式為 YYYY-MM-DD")
    adults: Optional[int] = Field(None, description="成人人數")
    children: Optional[int] = Field(None, description="兒童人數")

class HotelFuzzyMatchQuery(BaseModel):
    """模糊比對旅館名稱的查詢參數"""
    name: str = Field(..., description="旅館名稱")

class HotelDetailQuery(BaseModel):
    """獲取旅館詳細信息的查詢參數"""
    hotel_id: str = Field(..., description="旅館 ID")

class HotelSupplyQuery(BaseModel):
    """根據備品搜尋旅館的查詢參數"""
    supply_ids: List[str] = Field(..., description="備品 ID 列表")

class PlanQuery(BaseModel):
    """獲取旅館訂購方案的查詢參數"""
    hotel_id: str = Field(..., description="旅館 ID")
    keyword: Optional[str] = Field(None, description="關鍵字")

class VacancyQuery(BaseModel):
    """多條件搜尋可訂旅館空房的查詢參數"""
    county_id: Optional[str] = Field(None, description="縣市 ID")
    district_id: Optional[str] = Field(None, description="鄉鎮區 ID")
    hotel_type: Optional[List[str]] = Field(None, description="旅館類型 ID 列表")
    check_in_date: str = Field(..., description="入住日期，格式為 YYYY-MM-DD")
    check_out_date: str = Field(..., description="退房日期，格式為 YYYY-MM-DD")
    adults: int = Field(..., description="成人人數")
    children: Optional[int] = Field(0, description="兒童人數")
    min_price: Optional[int] = Field(None, description="最低價格")
    max_price: Optional[int] = Field(None, description="最高價格")

class NearbyPlaceQuery(BaseModel):
    """搜尋周邊地點的查詢參數"""
    query: str = Field(..., description="搜尋關鍵字")
    location: Optional[str] = Field(None, description="位置坐標 (經緯度)，格式為 'latitude,longitude'")
    radius: Optional[int] = Field(1000, description="搜尋半徑 (米)")

class SurroundingsMapQuery(BaseModel):
    """獲取周邊地圖圖像的查詢參數"""
    location: str = Field(..., description="位置坐標 (經緯度)，格式為 'latitude,longitude'")

class HotelAgent(BaseAgent):
    """
    旅宿推薦 Agent，負責處理旅宿相關查詢和推薦
    """
    
    def __init__(
        self,
        name: str = "旅宿專家",
        role: str = "旅宿推薦專家",
        goal: str = "為用戶提供最適合的旅宿推薦，滿足其預算、位置和設施需求",
        backstory: str = "我是一位經驗豐富的旅宿顧問，熟悉台灣各地的旅宿選擇，能夠根據用戶的需求提供最適合的推薦。",
        description: str = "負責處理旅宿相關查詢，提供旅宿推薦，並回答旅宿相關問題",
        **kwargs
    ):
        """
        初始化旅宿推薦 Agent
        
        Args:
            name: Agent 的名稱
            role: Agent 的角色
            goal: Agent 的目標
            backstory: Agent 的背景故事
            description: Agent 的描述
            **kwargs: 其他參數，傳遞給父類
        """
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            backstory=backstory,
            description=description,
            **kwargs
        )
        
        # 初始化 API 客戶端
        self.hotel_api = HotelAPI()
        self.place_api = PlaceAPI()
        
        # 初始化 OpenAI 客戶端
        openai.api_key = self.api_key
        
        # 定義工具函數
        self._define_tools()
    
    def _define_tools(self):
        """定義 Agent 可用的工具函數"""
        # 旅宿 API 工具
        self.tools = [
            self.get_counties,
            self.get_districts,
            self.get_hotel_types,
            self.get_hotel_facilities,
            self.get_room_facilities,
            self.get_bed_types,
            self.get_hotels,
            self.fuzzy_match_hotel,
            self.get_hotel_detail,
            self.search_hotels_by_supply,
            self.get_plans,
            self.search_vacancies,
            # 地點 API 工具
            self.search_nearby_places,
            self.get_surroundings_map
        ]
    
    async def get_counties(self, query: CountyQuery) -> List[Dict[str, Any]]:
        """
        獲取縣市列表
        
        Returns:
            List[Dict[str, Any]]: 縣市列表
        """
        if self.verbose:
            print(f"{self.name} 正在獲取縣市列表")
        return await self.hotel_api.get_counties()
    
    async def get_districts(self, query: DistrictQuery) -> List[Dict[str, Any]]:
        """
        獲取鄉鎮區列表
        
        Args:
            query: 查詢參數
            
        Returns:
            List[Dict[str, Any]]: 鄉鎮區列表
        """
        if self.verbose:
            print(f"{self.name} 正在獲取鄉鎮區列表，縣市 ID: {query.county_id}")
        return await self.hotel_api.get_districts(query.county_id)
    
    async def get_hotel_types(self, query: HotelTypeQuery) -> List[Dict[str, Any]]:
        """
        獲取旅館類型列表
        
        Returns:
            List[Dict[str, Any]]: 旅館類型列表
        """
        if self.verbose:
            print(f"{self.name} 正在獲取旅館類型列表")
        return await self.hotel_api.get_hotel_types()
    
    async def get_hotel_facilities(self, query: HotelFacilityQuery) -> List[str]:
        """
        獲取飯店設施列表
        
        Returns:
            List[str]: 飯店設施名稱列表
        """
        if self.verbose:
            print(f"{self.name} 正在獲取飯店設施列表")
        return await self.hotel_api.get_hotel_facilities()
    
    async def get_room_facilities(self, query: RoomFacilityQuery) -> List[str]:
        """
        獲取房間備品列表
        
        Returns:
            List[str]: 房間備品名稱列表
        """
        if self.verbose:
            print(f"{self.name} 正在獲取房間備品列表")
        return await self.hotel_api.get_room_facilities()
    
    async def get_bed_types(self, query: BedTypeQuery) -> List[Dict[str, Any]]:
        """
        獲取房間床型列表
        
        Returns:
            List[Dict[str, Any]]: 房間床型列表
        """
        if self.verbose:
            print(f"{self.name} 正在獲取房間床型列表")
        return await self.hotel_api.get_bed_types()
    
    async def get_hotels(self, query: HotelQuery) -> List[Dict[str, Any]]:
        """
        獲取旅館列表
        
        Args:
            query: 查詢參數
            
        Returns:
            List[Dict[str, Any]]: 旅館列表
        """
        params = query.dict(exclude_none=True)
        if self.verbose:
            print(f"{self.name} 正在獲取旅館列表，參數: {params}")
        return await self.hotel_api.get_hotels(params)
    
    async def fuzzy_match_hotel(self, query: HotelFuzzyMatchQuery) -> List[Dict[str, Any]]:
        """
        模糊比對旅館名稱
        
        Args:
            query: 查詢參數
            
        Returns:
            List[Dict[str, Any]]: 匹配的旅館列表
        """
        if self.verbose:
            print(f"{self.name} 正在模糊比對旅館名稱: {query.name}")
        return await self.hotel_api.fuzzy_match_hotel(query.name)
    
    async def get_hotel_detail(self, query: HotelDetailQuery) -> Dict[str, Any]:
        """
        獲取旅館詳細信息
        
        Args:
            query: 查詢參數
            
        Returns:
            Dict[str, Any]: 旅館詳細信息
        """
        if self.verbose:
            print(f"{self.name} 正在獲取旅館詳細信息，旅館 ID: {query.hotel_id}")
        return await self.hotel_api.get_hotel_detail(query.hotel_id)
    
    async def search_hotels_by_supply(self, query: HotelSupplyQuery) -> List[Dict[str, Any]]:
        """
        根據備品搜尋旅館
        
        Args:
            query: 查詢參數
            
        Returns:
            List[Dict[str, Any]]: 旅館列表
        """
        if self.verbose:
            print(f"{self.name} 正在根據備品搜尋旅館，備品 ID: {query.supply_ids}")
        return await self.hotel_api.search_hotels_by_supply(query.supply_ids)
    
    async def get_plans(self, query: PlanQuery) -> List[Dict[str, Any]]:
        """
        獲取旅館訂購方案
        
        Args:
            query: 查詢參數
            
        Returns:
            List[Dict[str, Any]]: 訂購方案列表
        """
        if self.verbose:
            print(f"{self.name} 正在獲取旅館訂購方案，旅館 ID: {query.hotel_id}，關鍵字: {query.keyword}")
        return await self.hotel_api.get_plans(query.hotel_id, query.keyword)
    
    async def search_vacancies(self, query: VacancyQuery) -> List[Dict[str, Any]]:
        """
        多條件搜尋可訂旅館空房
        
        Args:
            query: 查詢參數
            
        Returns:
            List[Dict[str, Any]]: 可訂旅館空房列表
        """
        params = query.dict(exclude_none=True)
        if self.verbose:
            print(f"{self.name} 正在搜尋可訂旅館空房，參數: {params}")
        return await self.hotel_api.search_vacancies(params)
    
    async def search_nearby_places(self, query: NearbyPlaceQuery) -> Dict[str, Any]:
        """
        搜尋周邊地點
        
        Args:
            query: 查詢參數
            
        Returns:
            Dict[str, Any]: 搜尋結果，包含地圖圖像和地點列表
        """
        if self.verbose:
            print(f"{self.name} 正在搜尋周邊地點，關鍵字: {query.query}，位置: {query.location}，半徑: {query.radius}")
        return await self.place_api.search_nearby_places(query.query, query.location, query.radius)
    
    async def get_surroundings_map(self, query: SurroundingsMapQuery) -> str:
        """
        獲取周邊地圖圖像
        
        Args:
            query: 查詢參數
            
        Returns:
            str: 地圖圖像 URL
        """
        if self.verbose:
            print(f"{self.name} 正在獲取周邊地圖圖像，位置: {query.location}")
        return await self.place_api.get_surroundings_map(query.location)
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行任務
        
        Args:
            task: 任務數據，包含用戶的查詢和其他參數
            
        Returns:
            任務執行結果
        """
        # 獲取用戶查詢
        user_query = task.get("query", "")
        task_type = task.get("type", "hotel_recommendation")
        parameters = task.get("parameters", {})
        
        if self.verbose:
            print(f"[HotelAgent] 收到任務: {task_type}")
            print(f"[HotelAgent] 用戶查詢: {user_query[:50]}...")
            print(f"[HotelAgent] 參數: {parameters}")
        
        # 根據任務類型執行不同的處理邏輯
        if task_type == "hotel_recommendation":
            result = self._process_hotel_recommendation(user_query, parameters)
        else:
            result = {
                "status": "error",
                "message": f"不支持的任務類型: {task_type}",
                "data": None
            }
            if self.verbose:
                print(f"[HotelAgent] 不支持的任務類型: {task_type}")
        
        if self.verbose:
            print(f"[HotelAgent] 任務完成，結果狀態: {result.get('status', 'unknown')}")
        
        return result
    
    def _process_hotel_recommendation(self, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理旅宿推薦任務
        
        Args:
            query: 用戶查詢
            parameters: 任務參數
            
        Returns:
            處理結果
        """
        # 使用 LLM 進行 function calling
        try:
            if self.verbose:
                print(f"[HotelAgent] 開始處理旅宿推薦任務...")
            
            # 準備 function 定義
            if self.verbose:
                print(f"[HotelAgent] 準備 function 定義...")
            functions = self._prepare_functions()
            if self.verbose:
                print(f"[HotelAgent] 準備了 {len(functions)} 個 function 定義")
            
            # 準備系統提示詞
            if self.verbose:
                print(f"[HotelAgent] 準備系統提示詞...")
            system_prompt = self._prepare_system_prompt(parameters)
            
            # 準備用戶提示詞
            if self.verbose:
                print(f"[HotelAgent] 準備用戶提示詞...")
            user_prompt = self._prepare_user_prompt(query, parameters)
            
            # 調用 OpenAI API
            if self.verbose:
                print(f"[HotelAgent] 調用 OpenAI API...")
            
            try:
                response = openai.chat.completions.create(
                    model=self.llm,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    tools=functions,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=4000
                )
                
                if self.verbose:
                    print(f"[HotelAgent] 收到 OpenAI 回應")
                    if response.choices and response.choices[0].message:
                        message = response.choices[0].message
                        print(f"[HotelAgent] 回應內容: {message.content[:50] if message.content else 'No content'}...")
                        if message.tool_calls:
                            print(f"[HotelAgent] 工具調用數量: {len(message.tool_calls)}")
                            for i, tool_call in enumerate(message.tool_calls):
                                print(f"[HotelAgent] 工具調用 {i+1}: {tool_call.function.name}")
            except Exception as e:
                if self.verbose:
                    print(f"[HotelAgent] 調用 OpenAI API 時發生錯誤: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                raise
            
            # 處理 LLM 回應
            if self.verbose:
                print(f"[HotelAgent] 處理 LLM 回應...")
            result = self._process_llm_response(response, query, parameters)
            
            if self.verbose:
                print(f"[HotelAgent] 處理完成，推薦文本長度: {len(result.get('recommendation', ''))}")
                print(f"[HotelAgent] 使用的工具: {result.get('tools_used', [])}")
            
            return {
                "status": "success",
                "message": "旅宿推薦任務已完成",
                "data": result
            }
        except Exception as e:
            if self.verbose:
                print(f"[HotelAgent] 處理旅宿推薦任務時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
            
            return {
                "status": "error",
                "message": f"處理旅宿推薦任務時發生錯誤: {str(e)}",
                "data": None
            }
    
    def _prepare_functions(self) -> List[Dict[str, Any]]:
        """
        準備 function 定義
        
        Returns:
            List[Dict[str, Any]]: function 定義列表
        """
        functions = []
        
        # 為每個工具函數創建 function 定義
        for tool in self.tools:
            # 獲取函數的參數類型
            param_type = tool.__annotations__.get("query", None)
            
            if param_type and issubclass(param_type, BaseModel):
                # 創建 function 定義
                function_def = {
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": tool.__doc__,
                        "parameters": param_type.schema()
                    }
                }
                
                functions.append(function_def)
                
                if self.verbose:
                    print(f"[_prepare_functions] 添加工具: {tool.__name__}")
        
        return functions
    
    def _prepare_system_prompt(self, parameters: Dict[str, Any]) -> str:
        """
        準備系統提示詞
        
        Args:
            parameters: 任務參數
            
        Returns:
            str: 系統提示詞
        """
        return f"""
        你是 {self.name}，一個 {self.role}。你的目標是: {self.goal}
        
        背景: {self.backstory}
        
        你有以下工具可以使用:
        1. get_counties - 獲取台灣縣市列表
        2. get_districts - 獲取特定縣市的鄉鎮區列表
        3. get_hotel_types - 獲取旅館類型列表
        4. get_hotel_facilities - 獲取飯店設施列表
        5. get_room_facilities - 獲取房間備品列表
        6. get_bed_types - 獲取房間床型列表
        7. get_hotels - 根據條件獲取旅館列表
        8. fuzzy_match_hotel - 模糊比對旅館名稱
        9. get_hotel_detail - 獲取旅館詳細信息
        10. search_hotels_by_supply - 根據備品搜尋旅館
        11. get_plans - 獲取旅館訂購方案
        12. search_vacancies - 多條件搜尋可訂旅館空房
        13. search_nearby_places - 搜尋周邊地點
        14. get_surroundings_map - 獲取周邊地圖圖像
        
        工作流程:
        1. 了解用戶需求（地點、日期、人數、預算等）
        2. 使用適當工具獲取相關信息
        3. 根據用戶需求提供具體旅宿推薦
        4. 提供推薦理由（位置、價格、設施等）
        
        回應要求:
        - 使用繁體中文
        - 專業、友好、有幫助
        - 提供具體推薦，不要籠統建議
        - 多個推薦時列出優缺點比較
        """
    
    def _prepare_user_prompt(self, query: str, parameters: Dict[str, Any]) -> str:
        """
        準備用戶提示詞
        
        Args:
            query: 用戶查詢
            parameters: 任務參數
            
        Returns:
            str: 用戶提示詞
        """
        # 如果有表單數據，添加到提示詞中
        form_data_prompt = ""
        if parameters:
            form_data_prompt = "用戶提供的表單數據:\n"
            for key, value in parameters.items():
                form_data_prompt += f"- {key}: {value}\n"
        
        return f"""
        用戶查詢: {query}
        
        {form_data_prompt}
        
        請使用適當的工具來幫助用戶找到最適合的旅宿。如需更多信息，請告知用戶。
        """
    
    def _process_llm_response(self, response, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理 LLM 回應
        
        Args:
            response: LLM 回應
            query: 用戶查詢
            parameters: 任務參數
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        # 獲取 LLM 回應的內容
        message = response.choices[0].message
        
        if self.verbose:
            print(f"[_process_llm_response] 開始處理 LLM 回應...")
        
        # 如果沒有 tool_calls，直接返回 LLM 的回應
        if not message.tool_calls:
            if self.verbose:
                print(f"[_process_llm_response] 沒有工具調用，直接返回 LLM 回應")
            return {
                "recommendation": message.content,
                "tools_used": []
            }
        
        # 創建一個新的消息列表，包含系統提示詞和用戶查詢
        messages = [
            {"role": "system", "content": self._prepare_system_prompt(parameters)},
            {"role": "user", "content": self._prepare_user_prompt(query, parameters)}
        ]
        
        # 添加 assistant 的回應
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in message.tool_calls
            ]
        })
        
        if self.verbose:
            print(f"[_process_llm_response] 處理 {len(message.tool_calls)} 個工具調用")
        
        # 處理每個 tool_call
        tools_used = []
        for tool_call in message.tool_calls:
            # 獲取工具名稱和參數
            tool_name = tool_call.function.name
            tools_used.append(tool_name)
            
            if self.verbose:
                print(f"[_process_llm_response] 處理工具調用: {tool_name}")
            
            try:
                # 解析參數
                tool_args = json.loads(tool_call.function.arguments)
                if self.verbose:
                    print(f"[_process_llm_response] 工具參數: {tool_args}")
                
                # 查找對應的工具函數
                tool_func = next((tool for tool in self.tools if tool.__name__ == tool_name), None)
                
                if tool_func:
                    # 獲取參數類型
                    param_type = tool_func.__annotations__.get("query", None)
                    
                    if param_type and issubclass(param_type, BaseModel):
                        # 創建參數對象
                        param_obj = param_type(**tool_args)
                        
                        # 執行工具函數
                        if self.verbose:
                            print(f"[_process_llm_response] 執行工具函數: {tool_name}")
                        
                        loop = asyncio.get_event_loop()
                        tool_result = loop.run_until_complete(tool_func(param_obj))
                        
                        if self.verbose:
                            print(f"[_process_llm_response] 工具執行結果: {str(tool_result)[:100]}...")
                        
                        # 添加工具結果到消息列表
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result, ensure_ascii=False)
                        })
                    else:
                        error_msg = f"工具 {tool_name} 的參數類型無效"
                        if self.verbose:
                            print(f"[_process_llm_response] 錯誤: {error_msg}")
                        raise ValueError(error_msg)
                else:
                    error_msg = f"找不到工具 {tool_name}"
                    if self.verbose:
                        print(f"[_process_llm_response] 錯誤: {error_msg}")
                    raise ValueError(error_msg)
            except Exception as e:
                if self.verbose:
                    print(f"[_process_llm_response] 執行工具 {tool_name} 時發生錯誤: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                
                # 添加錯誤信息到消息列表
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                })
        
        # 再次調用 OpenAI API 獲取最終回應
        try:
            if self.verbose:
                print(f"[_process_llm_response] 再次調用 OpenAI API 獲取最終回應...")
            
            final_response = openai.chat.completions.create(
                model=self.llm,
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            # 獲取最終回應的內容
            final_content = final_response.choices[0].message.content
            
            if self.verbose:
                print(f"[_process_llm_response] 獲取最終回應成功: {final_content[:100]}...")
            
            return {
                "recommendation": final_content,
                "tools_used": tools_used
            }
        except Exception as e:
            if self.verbose:
                print(f"[_process_llm_response] 獲取最終回應時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
            
            # 如果獲取最終回應失敗，返回原始回應
            return {
                "recommendation": message.content,
                "tools_used": tools_used,
                "error": str(e)
            } 