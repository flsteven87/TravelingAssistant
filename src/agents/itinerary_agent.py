"""
行程規劃 Agent，負責處理行程相關查詢和推薦
"""
from typing import Dict, List, Any, Optional, Union, Callable
import json
import asyncio
import openai
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from .base_agent import BaseAgent
from ..api.place_api import PlaceAPI

# 定義 Pydantic 模型用於 function calling
class PlaceQuery(BaseModel):
    """搜尋周邊地點的查詢參數"""
    query: str = Field(..., description="搜尋關鍵字，例如'餐廳'、'景點'、'博物館'等")
    location: Optional[str] = Field(None, description="位置坐標 (經緯度)，格式為 'latitude,longitude'")
    radius: Optional[int] = Field(1000, description="搜尋半徑 (米)，默認為 1000 米")

class ItineraryAgent(BaseAgent):
    """
    行程規劃 Agent，負責處理行程相關查詢和推薦
    """
    
    def __init__(
        self,
        name: str = "行程專家",
        role: str = "行程規劃專家",
        goal: str = "為用戶提供最適合的行程規劃，包括景點推薦、餐廳建議和交通安排",
        backstory: str = "我是一位經驗豐富的行程規劃師，熟悉台灣各地的景點和活動，能夠根據用戶的需求提供最適合的行程安排。",
        description: str = "負責處理行程相關查詢，提供景點推薦，並回答行程相關問題",
        **kwargs
    ):
        """
        初始化行程規劃 Agent
        
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
        self.place_api = PlaceAPI()
        
        # 初始化 OpenAI 客戶端
        openai.api_key = self.api_key
        
        # 定義工具函數
        self._define_tools()
    
    def _define_tools(self):
        """定義 Agent 可用的工具函數"""
        # 地點 API 工具
        self.tools = [
            self.search_nearby_places,
            self.get_surroundings_map
        ]
    
    async def search_nearby_places(self, query: PlaceQuery) -> Dict[str, Any]:
        """
        搜尋周邊地點
        
        Args:
            query: 查詢參數
            
        Returns:
            Dict[str, Any]: 搜尋結果，包含地圖圖像和地點列表
        """
        if self.verbose:
            print(f"{self.name} 正在搜尋周邊地點，關鍵字: {query.query}, 位置: {query.location}, 半徑: {query.radius}米")
        
        return await self.place_api.search_nearby_places(
            query=query.query,
            location=query.location,
            radius=query.radius
        )
    
    async def get_surroundings_map(self, location: str) -> str:
        """
        獲取周邊地圖圖像
        
        Args:
            location: 位置坐標 (經緯度)，格式為 "latitude,longitude"
            
        Returns:
            str: 地圖圖像 URL
        """
        if self.verbose:
            print(f"{self.name} 正在獲取周邊地圖，位置: {location}")
        
        return await self.place_api.get_surroundings_map(location)
    
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
        task_type = task.get("type", "itinerary_planning")
        parameters = task.get("parameters", {})
        
        if self.verbose:
            print(f"[ItineraryAgent] 收到任務: {task_type}")
            print(f"[ItineraryAgent] 用戶查詢: {user_query[:50]}...")
            print(f"[ItineraryAgent] 參數: {parameters}")
        
        # 根據任務類型執行不同的處理邏輯
        if task_type == "itinerary_planning":
            result = self._process_itinerary_planning(user_query, parameters)
        else:
            result = {
                "status": "error",
                "message": f"不支持的任務類型: {task_type}",
                "data": None
            }
            if self.verbose:
                print(f"[ItineraryAgent] 不支持的任務類型: {task_type}")
        
        if self.verbose:
            print(f"[ItineraryAgent] 任務完成，結果狀態: {result.get('status', 'unknown')}")
        
        return result
    
    def _process_itinerary_planning(self, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理行程規劃任務
        
        Args:
            query: 用戶查詢
            parameters: 任務參數
            
        Returns:
            處理結果
        """
        try:
            # 準備系統提示詞
            system_prompt = self._prepare_system_prompt(parameters)
            
            # 準備用戶提示詞
            user_prompt = self._prepare_user_prompt(query, parameters)
            
            # 準備函數定義
            functions = self._prepare_functions()
            
            if self.verbose:
                print(f"[ItineraryAgent] 調用 OpenAI API...")
            
            # 調用 OpenAI API
            try:
                # 使用 OpenAI 客戶端
                client = openai.OpenAI(api_key=self.api_key)
                
                # 創建聊天完成
                response = client.chat.completions.create(
                    model=self.llm,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    tools=functions,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=1500
                )
                
                if self.verbose:
                    print(f"[ItineraryAgent] 收到 OpenAI 回應")
                    if response.choices and response.choices[0].message:
                        message = response.choices[0].message
                        print(f"[ItineraryAgent] 回應內容: {message.content[:100] if message.content else 'No content'}...")
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            print(f"[ItineraryAgent] 工具調用數量: {len(message.tool_calls)}")
                            for i, tool_call in enumerate(message.tool_calls):
                                print(f"[ItineraryAgent] 工具調用 {i+1}: {tool_call.function.name}")
                                print(f"[ItineraryAgent] 工具參數: {tool_call.function.arguments[:100]}...")
            except Exception as e:
                if self.verbose:
                    print(f"[ItineraryAgent] 調用 OpenAI API 時發生錯誤: {str(e)}")
                raise
            
            # 處理回應
            return self._process_llm_response(response, query, parameters)
            
        except Exception as e:
            if self.verbose:
                print(f"[ItineraryAgent] 處理行程規劃任務時發生錯誤: {str(e)}")
            
            return {
                "status": "error",
                "message": f"處理行程規劃任務時發生錯誤: {str(e)}",
                "data": {
                    "quick_response": "抱歉，我在處理您的請求時遇到了問題。請稍後再試。",
                    "complete_response": f"抱歉，我在處理您的行程規劃請求時遇到了技術問題。錯誤信息: {str(e)}。請稍後再試或者換一種方式提問。",
                    "tools_used": []
                }
            }
    
    def _prepare_functions(self) -> List[Dict[str, Any]]:
        """
        準備 function 定義
        
        Returns:
            List[Dict[str, Any]]: function 定義列表
        """
        if self.verbose:
            print(f"[_prepare_functions] 開始準備工具函數定義...")
        
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "search_nearby_places",
                    "description": "搜尋指定位置周邊的地點，如餐廳、景點、博物館等。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜尋關鍵字，例如'餐廳'、'景點'、'博物館'等"
                            },
                            "location": {
                                "type": "string",
                                "description": "位置坐標 (經緯度)，格式為 'latitude,longitude'"
                            },
                            "radius": {
                                "type": "integer",
                                "description": "搜尋半徑 (米)，默認為 1000 米"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_surroundings_map",
                    "description": "獲取指定位置的周邊地圖圖像。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "位置坐標 (經緯度)，格式為 'latitude,longitude'"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        if self.verbose:
            print(f"[_prepare_functions] 準備了 {len(functions)} 個工具函數定義")
        
        return functions
    
    def _prepare_system_prompt(self, parameters: Dict[str, Any]) -> str:
        """
        準備系統提示詞
        
        Args:
            parameters: 任務參數
            
        Returns:
            str: 系統提示詞
        """
        # 從參數中提取相關信息
        location = parameters.get("location", "")
        hotel_name = parameters.get("hotel_name", "")
        hotel_location = parameters.get("hotel_location", "")
        interests = parameters.get("interests", [])
        duration = parameters.get("duration", 1)
        
        # 將興趣列表轉換為字符串
        interests_str = ", ".join(interests) if interests else "未指定"
        
        # 構建系統提示詞
        system_prompt = f"""你是一位專業的行程規劃專家，負責為用戶提供行程建議和景點推薦。

你的任務是根據用戶的需求，規劃合適的行程，包括景點推薦、餐廳建議和交通安排。

用戶信息:
- 目的地: {location}
- 住宿地點: {hotel_name}
- 住宿位置: {hotel_location}
- 行程天數: {duration} 天
- 興趣愛好: {interests_str}

你可以使用以下工具來獲取信息:
1. search_nearby_places: 搜尋指定位置周邊的地點，如餐廳、景點、博物館等
2. get_surroundings_map: 獲取指定位置的周邊地圖圖像

請根據用戶的需求，使用這些工具來獲取相關信息，並提供合適的行程規劃。

回應格式要求:
1. 使用繁體中文回應
2. 提供簡潔明了的行程安排
3. 如果用戶沒有提供足夠的信息，請禮貌地詢問更多細節
4. 行程安排應包括:
   - 每天的行程概述
   - 推薦的景點和活動
   - 餐廳建議
   - 交通安排
   - 時間安排建議
"""
        
        return system_prompt
    
    def _prepare_user_prompt(self, query: str, parameters: Dict[str, Any]) -> str:
        """
        準備用戶提示詞
        
        Args:
            query: 用戶查詢
            parameters: 任務參數
            
        Returns:
            str: 用戶提示詞
        """
        # 直接使用用戶的查詢作為提示詞
        user_prompt = query
        
        # 如果有額外的參數，添加到提示詞中
        if parameters:
            user_prompt += "\n\n額外信息:\n"
            for key, value in parameters.items():
                if key != "query":  # 避免重複添加查詢
                    user_prompt += f"- {key}: {value}\n"
        
        return user_prompt
    
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
        if self.verbose:
            print(f"[ItineraryAgent] 開始處理 LLM 回應...")
        
        # 初始化結果
        result = {
            "status": "success",
            "message": "行程規劃完成",
            "data": {
                "quick_response": "我正在為您規劃行程，請稍等...",
                "complete_response": "",
                "tools_used": []
            }
        }
        
        # 處理 LLM 回應
        if response.choices and response.choices[0].message:
            message = response.choices[0].message
            
            # 如果有工具調用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # 處理工具調用
                tool_results = []
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if self.verbose:
                        print(f"[ItineraryAgent] 處理工具調用: {function_name}")
                        print(f"[ItineraryAgent] 工具參數: {function_args}")
                    
                    # 記錄工具使用
                    result["data"]["tools_used"].append({
                        "tool": function_name,
                        "parameters": function_args
                    })
                    
                    # 執行工具調用
                    if function_name == "search_nearby_places":
                        # 創建查詢對象
                        place_query = PlaceQuery(**function_args)
                        # 執行查詢
                        tool_result = asyncio.run(self.search_nearby_places(place_query))
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "function_name": function_name,
                            "result": tool_result
                        })
                    elif function_name == "get_surroundings_map":
                        # 獲取位置參數
                        location = function_args.get("location", "")
                        # 獲取地圖
                        tool_result = asyncio.run(self.get_surroundings_map(location))
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "function_name": function_name,
                            "result": tool_result
                        })
                
                # 如果有工具結果，繼續與 LLM 對話
                if tool_results:
                    if self.verbose:
                        print(f"[ItineraryAgent] 繼續與 LLM 對話，傳遞工具結果...")
                    
                    # 構建新的消息列表
                    messages = [
                        {"role": "system", "content": self._prepare_system_prompt(parameters)},
                        {"role": "user", "content": self._prepare_user_prompt(query, parameters)},
                        {"role": "assistant", "content": message.content or "", "tool_calls": message.tool_calls}
                    ]
                    
                    # 添加工具結果
                    for tool_result in tool_results:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_result["tool_call_id"],
                            "name": tool_result["function_name"],
                            "content": json.dumps(tool_result["result"], ensure_ascii=False)
                        })
                    
                    # 再次調用 LLM
                    try:
                        client = openai.OpenAI(api_key=self.api_key)
                        second_response = client.chat.completions.create(
                            model=self.llm,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=1500
                        )
                        
                        if second_response.choices and second_response.choices[0].message:
                            final_message = second_response.choices[0].message
                            result["data"]["complete_response"] = final_message.content or "抱歉，我無法為您提供行程規劃。"
                        else:
                            result["data"]["complete_response"] = "抱歉，我無法為您提供行程規劃。"
                    except Exception as e:
                        if self.verbose:
                            print(f"[ItineraryAgent] 第二次調用 LLM 時發生錯誤: {str(e)}")
                        result["data"]["complete_response"] = "抱歉，在處理您的行程規劃時發生了錯誤。"
                else:
                    # 如果沒有工具結果，直接使用 LLM 的回應
                    result["data"]["complete_response"] = message.content or "抱歉，我無法為您提供行程規劃。"
            else:
                # 如果沒有工具調用，直接使用 LLM 的回應
                result["data"]["complete_response"] = message.content or "抱歉，我無法為您提供行程規劃。"
        else:
            # 如果沒有回應，返回錯誤信息
            result["status"] = "error"
            result["message"] = "無法獲取 LLM 回應"
            result["data"]["complete_response"] = "抱歉，我無法為您提供行程規劃。"
        
        # 設置快速回應
        if not result["data"]["quick_response"]:
            result["data"]["quick_response"] = "我正在為您規劃行程，請稍等..."
        
        if self.verbose:
            print(f"[ItineraryAgent] LLM 回應處理完成")
        
        return result 