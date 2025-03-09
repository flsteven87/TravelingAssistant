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

# 定義 Pydantic 模型用於 function calling
class HotelQuery(BaseModel):
    """獲取旅館列表的查詢參數"""
    page: Optional[int] = Field(None, description="頁碼")
    per_page: Optional[int] = Field(None, description="每頁數量")
    id: Optional[str] = Field(None, description="旅館 ID，用於獲取特定旅館的詳細信息")
    hotel_group_types: Optional[List[str]] = Field(None, description="旅館類型列表，例如 ['BASIC', 'SPA', 'PET_HOTEL']")

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
        
        # 初始化 OpenAI 客戶端
        openai.api_key = self.api_key
        
        # 定義工具函數
        self._define_tools()
    
    def _define_tools(self):
        """定義 Agent 可用的工具函數"""
        # 旅宿 API 工具 - 只保留 get_hotels 函數
        self.tools = [
            self.get_hotels
        ]
    
    async def get_hotels(self, query: HotelQuery) -> List[Dict[str, Any]]:
        """
        獲取旅館列表
        
        Args:
            query: 查詢參數
            
        Returns:
            List[Dict[str, Any]]: 旅館列表
        """
        params = {}
        if query.page is not None:
            params["page"] = query.page
        if query.per_page is not None:
            params["per_page"] = query.per_page
        if query.id is not None:
            params["id"] = query.id
        if query.hotel_group_types is not None and len(query.hotel_group_types) > 0:
            params["hotel_group_types"] = ",".join(query.hotel_group_types)
        
        if self.verbose:
            print(f"{self.name} 正在獲取旅館列表，參數: {params}")
        return await self.hotel_api.get_hotels(params)
    
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
        try:
            # 準備系統提示詞
            system_prompt = self._prepare_system_prompt(parameters)
            
            # 準備用戶提示詞
            user_prompt = self._prepare_user_prompt(query, parameters)
            
            # 準備函數定義
            functions = self._prepare_functions()
            
            if self.verbose:
                print(f"[HotelAgent] 調用 OpenAI API...")
            
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
                    print(f"[HotelAgent] 收到 OpenAI 回應")
                    if response.choices and response.choices[0].message:
                        message = response.choices[0].message
                        print(f"[HotelAgent] 回應內容: {message.content[:100] if message.content else 'No content'}...")
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            print(f"[HotelAgent] 工具調用數量: {len(message.tool_calls)}")
                            for i, tool_call in enumerate(message.tool_calls):
                                print(f"[HotelAgent] 工具調用 {i+1}: {tool_call.function.name}")
                                print(f"[HotelAgent] 工具參數: {tool_call.function.arguments[:100]}...")
            except Exception as e:
                if self.verbose:
                    print(f"[HotelAgent] 調用 OpenAI API 時發生錯誤: {str(e)}")
                raise
            
            # 處理回應
            return self._process_llm_response(response, query, parameters)
            
        except Exception as e:
            if self.verbose:
                print(f"[HotelAgent] 處理旅宿推薦任務時發生錯誤: {str(e)}")
            
            return {
                "status": "error",
                "message": f"處理旅宿推薦任務時發生錯誤: {str(e)}",
                "data": {
                    "quick_response": "抱歉，我在處理您的請求時遇到了問題。請稍後再試。",
                    "complete_response": f"抱歉，我在處理您的旅宿推薦請求時遇到了技術問題。錯誤信息: {str(e)}。請稍後再試或者換一種方式提問。",
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
        
        # 只保留 get_hotels 函數定義，使用更簡單的定義方式
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "get_hotels",
                    "description": "根據條件獲取旅館列表，如頁碼、每頁數量、特定旅館 ID 或旅館類型。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "page": {
                                "type": "integer",
                                "description": "頁碼，默認為 1"
                            },
                            "per_page": {
                                "type": "integer",
                                "description": "每頁數量，默認為 10"
                            },
                            "id": {
                                "type": "string",
                                "description": "旅館 ID，用於獲取特定旅館的詳細信息"
                            },
                            "hotel_group_types": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "旅館類型列表，例如 ['BASIC', 'SPA', 'PET_HOTEL', 'CHECKINN', 'PARENT_CHILD_FRIENDLY', 'SUITABLE_FOR_OFFICE']"
                            }
                        }
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
        # 從參數中提取旅館類型
        hotel_types = parameters.get("hotel_types", [])
        hotel_types_str = ", ".join(hotel_types) if hotel_types else "無特別偏好"
        
        system_prompt = f"""
        你是 {self.name}，一個 {self.role}。
        
        你的目標是: {self.goal}
        
        背景: {self.backstory}
        
        你需要根據用戶的需求提供旅宿推薦。你可以使用以下工具來獲取旅宿信息:
        
        1. get_hotels: 獲取旅館列表，可以根據旅館類型進行篩選
        
        旅館類型列表及其代碼:
        - BASIC: 主推
        - SPA: 溫泉
        - PET_HOTEL: 寵物飯店
        - CHECKINN: 雀客
        - PARENT_CHILD_FRIENDLY: 親子友善
        - SUITABLE_FOR_OFFICE: 適合辦公室
        
        用戶偏好的旅館類型: {hotel_types_str}
        
        請根據用戶的需求，使用 get_hotels 工具來獲取旅館信息，並在調用時使用 hotel_group_types 參數指定旅館類型。
        
        回應格式要求:
        1. 使用繁體中文回應
        2. 提供簡潔明了的旅宿推薦
        3. 如果用戶沒有提供足夠的信息，請禮貌地詢問更多細節
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
        try:
            # 獲取回應內容
            message = response.choices[0].message
            content = message.content or ""
            
            # 初始化工具使用記錄
            tools_used = []
            
            # 中文旅館類型名稱到英文代碼的映射
            hotel_type_mapping = {
                "主推": "BASIC",
                "溫泉": "SPA",
                "寵物飯店": "PET_HOTEL",
                "雀客": "CHECKINN",
                "親子友善": "PARENT_CHILD_FRIENDLY",
                "適合辦公室": "SUITABLE_FOR_OFFICE"
            }
            
            # 從參數中提取旅館類型並轉換為英文代碼
            hotel_types = parameters.get("hotel_types", [])
            hotel_type_codes = []
            for hotel_type in hotel_types:
                if hotel_type in hotel_type_mapping:
                    hotel_type_codes.append(hotel_type_mapping[hotel_type])
            
            # 處理工具調用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # 記錄工具使用
                    tools_used.append({
                        "name": function_name,
                        "arguments": function_args
                    })
                    
                    if self.verbose:
                        print(f"[HotelAgent] 調用工具: {function_name}, 參數: {function_args}")
                    
                    # 執行工具調用
                    if function_name == "get_hotels":
                        # 如果 LLM 沒有指定旅館類型但用戶有提供，則添加到參數中
                        if "hotel_group_types" not in function_args and hotel_type_codes:
                            function_args["hotel_group_types"] = hotel_type_codes
                            if self.verbose:
                                print(f"[HotelAgent] 添加用戶指定的旅館類型: {hotel_type_codes}")
                        
                        # 創建查詢對象
                        hotel_query = HotelQuery(**function_args)
                        
                        # 執行異步函數
                        try:
                            # 使用 asyncio.run 會導致 "This event loop is already running" 錯誤
                            # 因此我們使用 asyncio.create_task 和 asyncio.gather 來執行異步函數
                            import asyncio
                            
                            # 檢查是否已經有事件循環在運行
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    if self.verbose:
                                        print(f"[HotelAgent] 事件循環已經在運行，使用 asyncio.create_task")
                                    # 創建一個協程任務
                                    task = asyncio.create_task(self.get_hotels(hotel_query))
                                    # 等待任務完成
                                    result = asyncio.run_coroutine_threadsafe(self.get_hotels(hotel_query), loop).result()
                                else:
                                    if self.verbose:
                                        print(f"[HotelAgent] 事件循環未運行，使用 loop.run_until_complete")
                                    # 使用事件循環運行協程
                                    result = loop.run_until_complete(self.get_hotels(hotel_query))
                            except RuntimeError:
                                if self.verbose:
                                    print(f"[HotelAgent] 無法獲取事件循環，創建新的事件循環")
                                # 創建新的事件循環
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                # 使用新的事件循環運行協程
                                result = loop.run_until_complete(self.get_hotels(hotel_query))
                        except Exception as e:
                            if self.verbose:
                                print(f"[HotelAgent] 執行異步函數時發生錯誤: {str(e)}")
                            result = []
                        
                        # 將結果添加到內容中
                        if result:
                            content += f"\n\n我找到了以下旅館:\n"
                            for i, hotel in enumerate(result[:5], 1):  # 只顯示前 5 個結果
                                name = hotel.get("name", "未知旅館")
                                address = hotel.get("address", "地址未知")
                                price = hotel.get("price", "價格未知")
                                hotel_type = hotel.get("hotel_group_type", "類型未知")
                                content += f"{i}. {name} - 地址: {address}, 價格: {price}, 類型: {hotel_type}\n"
                            
                            if len(result) > 5:
                                content += f"...還有 {len(result) - 5} 個結果未顯示\n"
            
            # 如果沒有工具調用但用戶有提供旅館類型，則主動調用 get_hotels
            if not tools_used and hotel_type_codes:
                if self.verbose:
                    print(f"[HotelAgent] 沒有工具調用但用戶有提供旅館類型，主動調用 get_hotels")
                
                # 創建查詢對象
                hotel_query = HotelQuery(page=1, per_page=5, hotel_group_types=hotel_type_codes)
                
                # 執行異步函數
                try:
                    # 使用 asyncio.run 會導致 "This event loop is already running" 錯誤
                    # 因此我們使用 asyncio.create_task 和 asyncio.gather 來執行異步函數
                    import asyncio
                    
                    # 檢查是否已經有事件循環在運行
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            if self.verbose:
                                print(f"[HotelAgent] 事件循環已經在運行，使用 asyncio.create_task")
                            # 創建一個協程任務
                            task = asyncio.create_task(self.get_hotels(hotel_query))
                            # 等待任務完成
                            result = asyncio.run_coroutine_threadsafe(self.get_hotels(hotel_query), loop).result()
                        else:
                            if self.verbose:
                                print(f"[HotelAgent] 事件循環未運行，使用 loop.run_until_complete")
                            # 使用事件循環運行協程
                            result = loop.run_until_complete(self.get_hotels(hotel_query))
                    except RuntimeError:
                        if self.verbose:
                            print(f"[HotelAgent] 無法獲取事件循環，創建新的事件循環")
                        # 創建新的事件循環
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        # 使用新的事件循環運行協程
                        result = loop.run_until_complete(self.get_hotels(hotel_query))
                except Exception as e:
                    if self.verbose:
                        print(f"[HotelAgent] 執行異步函數時發生錯誤: {str(e)}")
                    result = []
                
                # 將結果添加到內容中
                if result:
                    content += f"\n\n根據您喜好的旅館類型 {', '.join(hotel_types)}，我找到了以下旅館:\n"
                    for i, hotel in enumerate(result[:5], 1):  # 只顯示前 5 個結果
                        name = hotel.get("name", "未知旅館")
                        address = hotel.get("address", "地址未知")
                        price = hotel.get("price", "價格未知")
                        hotel_type = hotel.get("hotel_group_type", "類型未知")
                        content += f"{i}. {name} - 地址: {address}, 價格: {price}, 類型: {hotel_type}\n"
                    
                    if len(result) > 5:
                        content += f"...還有 {len(result) - 5} 個結果未顯示\n"
            
            # 生成快速回應和完整回應
            quick_response = "我正在為您尋找適合的旅宿選擇，請稍候..."
            complete_response = content
            
            return {
                "status": "success",
                "message": "成功處理旅宿推薦任務",
                "data": {
                    "quick_response": quick_response,
                    "complete_response": complete_response,
                    "tools_used": tools_used
                }
            }
            
        except Exception as e:
            if self.verbose:
                print(f"[HotelAgent] 處理 LLM 回應時發生錯誤: {str(e)}")
            
            return {
                "status": "error",
                "message": f"處理 LLM 回應時發生錯誤: {str(e)}",
                "data": {
                    "quick_response": "抱歉，我在處理您的請求時遇到了問題。請稍後再試。",
                    "complete_response": f"抱歉，我在處理您的旅宿推薦請求時遇到了技術問題。錯誤信息: {str(e)}。請稍後再試或者換一種方式提問。",
                    "tools_used": []
                }
            } 