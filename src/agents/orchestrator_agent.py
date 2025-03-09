from typing import Dict, List, Any, Optional
import time
import openai
import os
import json
from pydantic import BaseModel, Field
from .base_agent import BaseAgent

# 定義 Pydantic 模型用於 function calling
class UserIntentAnalysis(BaseModel):
    """分析用戶意圖的查詢參數"""
    query: str = Field(..., description="用戶的查詢文本")
    needs_hotel_recommendation: bool = Field(False, description="用戶是否需要旅宿推薦")
    needs_itinerary_planning: bool = Field(False, description="用戶是否需要行程規劃")
    explanation: str = Field("", description="分析結果的解釋")

class HotelParameters(BaseModel):
    """從用戶查詢中提取旅宿參數"""
    query: str = Field(..., description="用戶的查詢文本")
    location: Optional[str] = Field(None, description="目的地，如縣市名稱")
    check_in_date: Optional[str] = Field(None, description="入住日期，格式為 YYYY-MM-DD")
    check_out_date: Optional[str] = Field(None, description="退房日期，格式為 YYYY-MM-DD")
    adults: Optional[int] = Field(None, description="成人人數")
    children: Optional[int] = Field(None, description="兒童人數")
    budget_min: Optional[int] = Field(None, description="最低預算（每晚）")
    budget_max: Optional[int] = Field(None, description="最高預算（每晚）")
    hotel_types: Optional[List[str]] = Field(None, description="偏好的旅館類型")
    facilities: Optional[List[str]] = Field(None, description="偏好的設施")
    special_requirements: Optional[str] = Field(None, description="特殊需求")

class ItineraryParameters(BaseModel):
    """從用戶查詢中提取行程參數"""
    query: str = Field(..., description="用戶的查詢文本")
    location: Optional[str] = Field(None, description="目的地，如縣市名稱")
    start_date: Optional[str] = Field(None, description="開始日期，格式為 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="結束日期，格式為 YYYY-MM-DD")
    duration: Optional[int] = Field(None, description="行程天數")
    interests: Optional[List[str]] = Field(None, description="興趣愛好")
    transportation: Optional[str] = Field(None, description="交通方式")
    with_children: Optional[bool] = Field(None, description="是否有兒童")
    budget: Optional[str] = Field(None, description="預算範圍")

class OrchestratorAgent(BaseAgent):
    """
    協調者 Agent，負責與用戶對話並協調其他專業 Agent
    """
    
    def __init__(
        self,
        name: str = "旅遊助手",
        role: str = "旅遊顧問協調者",
        goal: str = "協調旅宿推薦和行程規劃，為用戶提供完整的旅遊解決方案",
        backstory: str = "我是一位經驗豐富的旅遊顧問，專門協調各類旅遊需求，確保用戶獲得最佳的旅遊體驗。",
        description: str = "負責與用戶對話，理解需求，並協調其他專業 Agent 完成任務",
        **kwargs
    ):
        """
        初始化協調者 Agent
        
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
        
        # 初始化 OpenAI 客戶端
        openai.api_key = self.api_key
        
        # 用戶對話歷史
        self.conversation_history = []
        
        # 任務狀態
        self.current_task = None
        self.task_status = "idle"  # idle, processing, completed, failed
        self.task_progress = 0.0
        self.task_result = None
        
        # 快速回應時間限制 (5秒)
        self.quick_response_time = 5
        
        # 完整回應時間限制 (30秒)
        self.complete_response_time = 30
        
        # 定義 LLM 函數工具
        self._define_llm_tools()
    
    def _define_llm_tools(self):
        """定義 LLM 函數工具"""
        self.llm_tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_user_intent",
                    "description": "分析用戶意圖，判斷用戶是否需要旅宿推薦或行程規劃",
                    "parameters": UserIntentAnalysis.schema()
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_hotel_parameters",
                    "description": "從用戶查詢中提取旅宿參數",
                    "parameters": HotelParameters.schema()
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_itinerary_parameters",
                    "description": "從用戶查詢中提取行程參數",
                    "parameters": ItineraryParameters.schema()
                }
            }
        ]
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行任務
        
        Args:
            task: 任務數據，包含用戶的查詢和其他參數
            
        Returns:
            任務執行結果
        """
        # 記錄任務開始時間
        start_time = time.time()
        
        # 更新任務狀態
        self.current_task = task
        self.task_status = "processing"
        self.task_progress = 0.0
        self.task_result = None
        
        # 獲取用戶查詢
        user_query = task.get("query", "")
        
        if self.verbose:
            print(f"[OrchestratorAgent] 開始執行任務: {user_query[:50]}...")
        
        # 添加到對話歷史
        self.conversation_history.append({"role": "user", "content": user_query})
        
        # 生成快速回應 (5秒內)
        if self.verbose:
            print(f"[OrchestratorAgent] 生成快速回應...")
        quick_response = self._generate_quick_response(user_query)
        if self.verbose:
            print(f"[OrchestratorAgent] 快速回應: {quick_response}")
        
        # 更新進度
        self.task_progress = 0.3
        
        try:
            # 使用 LLM 分析用戶意圖
            if self.verbose:
                print(f"[OrchestratorAgent] 分析用戶意圖...")
            intent_analysis = self._analyze_user_intent(user_query)
            if self.verbose:
                print(f"[OrchestratorAgent] 意圖分析結果: {intent_analysis}")
            
            # 根據分析結果協調不同的 Agent
            if intent_analysis.get("needs_hotel_recommendation", False):
                # 提取旅宿參數
                if self.verbose:
                    print(f"[OrchestratorAgent] 提取旅宿參數...")
                hotel_params = self._extract_hotel_parameters_llm(user_query)
                if self.verbose:
                    print(f"[OrchestratorAgent] 旅宿參數: {hotel_params}")
                
                # 如果有旅宿推薦 Agent，則協調它
                hotel_agent = self._get_hotel_agent()
                if hotel_agent:
                    if self.verbose:
                        print(f"[OrchestratorAgent] 找到旅宿推薦 Agent: {hotel_agent.name}")
                    hotel_task = {
                        "query": user_query,
                        "type": "hotel_recommendation",
                        "parameters": hotel_params
                    }
                    if self.verbose:
                        print(f"[OrchestratorAgent] 委派任務給旅宿推薦 Agent...")
                    hotel_result = self.collaborate(hotel_agent, hotel_task)
                    if self.verbose:
                        print(f"[OrchestratorAgent] 旅宿推薦結果狀態: {hotel_result.get('status', 'unknown')}")
                    self.remember("hotel_recommendation", hotel_result)
                else:
                    if self.verbose:
                        print(f"[OrchestratorAgent] 未找到旅宿推薦 Agent")
            
            if intent_analysis.get("needs_itinerary_planning", False):
                if self.verbose:
                    print(f"[OrchestratorAgent] 需要行程規劃，但尚未實作 itinerary_agent，保留接口等待未來開發")
                # 保留接口等待未來開發
                pass
        except Exception as e:
            if self.verbose:
                print(f"[OrchestratorAgent] 協調 Agent 時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
        
        # 更新進度
        self.task_progress = 0.6
        
        # 生成完整回應
        if self.verbose:
            print(f"[OrchestratorAgent] 生成完整回應...")
        complete_response = self._generate_complete_response(user_query)
        if self.verbose:
            print(f"[OrchestratorAgent] 完整回應: {complete_response[:100]}...")
        
        # 更新進度
        self.task_progress = 1.0
        
        # 更新任務狀態
        self.task_status = "completed"
        
        # 記錄任務結束時間
        end_time = time.time()
        
        # 計算任務執行時間
        execution_time = end_time - start_time
        if self.verbose:
            print(f"[OrchestratorAgent] 任務完成，執行時間: {execution_time:.2f}秒")
        
        # 設置任務結果
        self.task_result = {
            "quick_response": quick_response,
            "complete_response": complete_response,
            "execution_time": execution_time
        }
        
        return self.task_result
    
    def _analyze_user_intent(self, query: str) -> Dict[str, Any]:
        """
        使用 LLM 分析用戶意圖
        
        Args:
            query: 用戶查詢
            
        Returns:
            分析結果
        """
        try:
            if self.verbose:
                print(f"[_analyze_user_intent] 開始分析用戶意圖...")
            
            # 準備系統提示詞
            system_prompt = f"""
            你是 {self.name}，一個 {self.role}。
            
            你的任務是分析用戶的查詢，判斷用戶是否需要旅宿推薦或行程規劃。
            
            旅宿推薦相關的關鍵詞包括：旅館、飯店、住宿、旅宿、民宿、酒店、住哪、住哪裡、哪裡住等。
            行程規劃相關的關鍵詞包括：行程、景點、玩什麼、去哪、去哪裡、遊玩、活動、規劃、安排等。
            
            請仔細分析用戶的查詢，判斷用戶的真實意圖。
            """
            
            if self.verbose:
                print(f"[_analyze_user_intent] 調用 OpenAI API...")
            
            # 調用 OpenAI API
            response = openai.chat.completions.create(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                tools=self.llm_tools[:1],  # 只使用 analyze_user_intent 工具
                tool_choice={"type": "function", "function": {"name": "analyze_user_intent"}},
                temperature=0.1,
                max_tokens=1000
            )
            
            # 獲取 LLM 回應的內容
            message = response.choices[0].message
            
            if self.verbose:
                print(f"[_analyze_user_intent] 收到 OpenAI 回應: {message.content[:50]}...")
                if message.tool_calls:
                    print(f"[_analyze_user_intent] 工具調用: {message.tool_calls[0].function.name}")
            
            # 如果有 tool_calls，處理它們
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                if tool_call.function.name == "analyze_user_intent":
                    result = json.loads(tool_call.function.arguments)
                    if self.verbose:
                        print(f"[_analyze_user_intent] 分析結果: {result}")
                    return result
            
            # 如果沒有 tool_calls，返回默認值
            if self.verbose:
                print(f"[_analyze_user_intent] 沒有工具調用，返回默認值")
            
            # 簡單的關鍵詞匹配作為備用方案
            hotel_keywords = ["旅館", "飯店", "住宿", "旅宿", "民宿", "酒店", "住哪", "住哪裡", "哪裡住"]
            itinerary_keywords = ["行程", "景點", "玩什麼", "去哪", "去哪裡", "遊玩", "活動", "規劃", "安排"]
            
            needs_hotel = any(keyword in query for keyword in hotel_keywords)
            needs_itinerary = any(keyword in query for keyword in itinerary_keywords)
            
            result = {
                "needs_hotel_recommendation": needs_hotel,
                "needs_itinerary_planning": needs_itinerary,
                "explanation": "使用關鍵詞匹配作為備用方案"
            }
            
            if self.verbose:
                print(f"[_analyze_user_intent] 備用分析結果: {result}")
            
            return result
        except Exception as e:
            if self.verbose:
                print(f"[_analyze_user_intent] 分析用戶意圖時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
            
            # 發生錯誤時，使用關鍵詞匹配作為備用方案
            hotel_keywords = ["旅館", "飯店", "住宿", "旅宿", "民宿", "酒店", "住哪", "住哪裡", "哪裡住"]
            itinerary_keywords = ["行程", "景點", "玩什麼", "去哪", "去哪裡", "遊玩", "活動", "規劃", "安排"]
            
            needs_hotel = any(keyword in query for keyword in hotel_keywords)
            needs_itinerary = any(keyword in query for keyword in itinerary_keywords)
            
            result = {
                "needs_hotel_recommendation": needs_hotel,
                "needs_itinerary_planning": needs_itinerary,
                "explanation": f"分析用戶意圖時發生錯誤: {str(e)}"
            }
            
            if self.verbose:
                print(f"[_analyze_user_intent] 錯誤後的備用分析結果: {result}")
            
            return result
    
    def _extract_hotel_parameters_llm(self, query: str) -> Dict[str, Any]:
        """
        使用 LLM 從用戶查詢中提取旅宿參數
        
        Args:
            query: 用戶查詢
            
        Returns:
            旅宿參數字典
        """
        try:
            if self.verbose:
                print(f"[_extract_hotel_parameters_llm] 開始提取旅宿參數...")
            
            # 準備系統提示詞
            system_prompt = f"""
            你是 {self.name}，一個 {self.role}。
            
            你的任務是從用戶的查詢中提取旅宿相關的參數，包括：
            - 目的地（縣市名稱）
            - 入住日期和退房日期
            - 成人和兒童人數
            - 預算範圍
            - 偏好的旅館類型
            - 偏好的設施
            - 特殊需求
            
            如果用戶沒有明確提供某些參數，請將對應的值設為 null。
            """
            
            if self.verbose:
                print(f"[_extract_hotel_parameters_llm] 調用 OpenAI API...")
            
            # 調用 OpenAI API
            response = openai.chat.completions.create(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                tools=self.llm_tools[1:2],  # 只使用 extract_hotel_parameters 工具
                tool_choice={"type": "function", "function": {"name": "extract_hotel_parameters"}},
                temperature=0.1,
                max_tokens=1000
            )
            
            # 獲取 LLM 回應的內容
            message = response.choices[0].message
            
            if self.verbose:
                print(f"[_extract_hotel_parameters_llm] 收到 OpenAI 回應: {message.content[:50]}...")
                if message.tool_calls:
                    print(f"[_extract_hotel_parameters_llm] 工具調用: {message.tool_calls[0].function.name}")
            
            # 如果有 tool_calls，處理它們
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                if tool_call.function.name == "extract_hotel_parameters":
                    result = json.loads(tool_call.function.arguments)
                    if self.verbose:
                        print(f"[_extract_hotel_parameters_llm] 提取結果: {result}")
                    return result
            
            # 如果沒有 tool_calls，返回默認值
            if self.verbose:
                print(f"[_extract_hotel_parameters_llm] 沒有工具調用，返回默認值")
            
            # 手動提取一些基本參數作為備用方案
            location = None
            check_in_date = None
            check_out_date = None
            adults = None
            children = None
            budget_min = None
            budget_max = None
            
            # 簡單的正則表達式匹配
            import re
            
            # 提取地點
            location_match = re.search(r'去([\w]+)[市縣]', query)
            if location_match:
                location = location_match.group(1) + "市" if "市" in query else location_match.group(1) + "縣"
            
            # 提取日期
            date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', query)
            if len(date_matches) >= 2:
                check_in_date = date_matches[0]
                check_out_date = date_matches[1]
            
            # 提取人數
            adults_match = re.search(r'(\d+)\s*位成人', query)
            if adults_match:
                adults = int(adults_match.group(1))
            
            children_match = re.search(r'(\d+)\s*位兒童', query)
            if children_match:
                children = int(children_match.group(1))
            
            # 提取預算
            budget_match = re.search(r'(\d+)\s*到\s*(\d+)\s*元', query)
            if budget_match:
                budget_min = int(budget_match.group(1))
                budget_max = int(budget_match.group(2))
            
            result = {
                "query": query,
                "location": location,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": adults,
                "children": children,
                "budget_min": budget_min,
                "budget_max": budget_max,
                "hotel_types": None,
                "facilities": None,
                "special_requirements": None
            }
            
            if self.verbose:
                print(f"[_extract_hotel_parameters_llm] 備用提取結果: {result}")
            
            return result
        except Exception as e:
            if self.verbose:
                print(f"[_extract_hotel_parameters_llm] 提取旅宿參數時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
            
            # 發生錯誤時，返回默認值
            result = {
                "query": query,
                "location": None,
                "check_in_date": None,
                "check_out_date": None,
                "adults": None,
                "children": None,
                "budget_min": None,
                "budget_max": None,
                "hotel_types": None,
                "facilities": None,
                "special_requirements": None
            }
            
            if self.verbose:
                print(f"[_extract_hotel_parameters_llm] 錯誤後的默認結果: {result}")
            
            return result
    
    def _extract_itinerary_parameters_llm(self, query: str) -> Dict[str, Any]:
        """
        使用 LLM 從用戶查詢中提取行程參數
        
        Args:
            query: 用戶查詢
            
        Returns:
            行程參數字典
        """
        try:
            # 準備系統提示詞
            system_prompt = f"""
            你是 {self.name}，一個 {self.role}。
            
            你的任務是從用戶的查詢中提取行程相關的參數，包括：
            - 目的地（縣市名稱）
            - 開始日期和結束日期
            - 行程天數
            - 興趣愛好
            - 交通方式
            - 是否有兒童
            - 預算範圍
            
            如果用戶沒有明確提供某些參數，請將對應的值設為 null。
            """
            
            # 調用 OpenAI API
            response = openai.chat.completions.create(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                tools=self.llm_tools[2:3],  # 只使用 extract_itinerary_parameters 工具
                tool_choice={"type": "function", "function": {"name": "extract_itinerary_parameters"}},
                temperature=0.1,
                max_tokens=1000
            )
            
            # 獲取 LLM 回應的內容
            message = response.choices[0].message
            
            # 如果有 tool_calls，處理它們
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                if tool_call.function.name == "extract_itinerary_parameters":
                    return json.loads(tool_call.function.arguments)
            
            # 如果沒有 tool_calls，返回默認值
            return {
                "query": query,
                "location": None,
                "start_date": None,
                "end_date": None,
                "duration": None,
                "interests": [],
                "transportation": None,
                "with_children": None,
                "budget": None
            }
        except Exception as e:
            if self.verbose:
                print(f"提取行程參數時發生錯誤: {str(e)}")
            
            # 發生錯誤時，返回默認值
            return {
                "query": query,
                "location": None,
                "start_date": None,
                "end_date": None,
                "duration": None,
                "interests": [],
                "transportation": None,
                "with_children": None,
                "budget": None
            }
    
    def _generate_quick_response(self, query: str) -> str:
        """
        生成快速回應
        
        Args:
            query: 用戶查詢
            
        Returns:
            快速回應
        """
        try:
            # 分析用戶意圖
            intent_analysis = self._analyze_user_intent(query)
            
            if intent_analysis.get("needs_hotel_recommendation", False):
                return "我正在為您尋找合適的旅宿選擇，請稍候..."
            elif intent_analysis.get("needs_itinerary_planning", False):
                return "我正在為您規劃行程，請稍候..."
            else:
                return "我正在處理您的請求，請稍候..."
        except Exception as e:
            if self.verbose:
                print(f"生成快速回應時發生錯誤: {str(e)}")
            return "我正在處理您的請求，請稍候..."
    
    def _generate_complete_response(self, query: str) -> str:
        """
        生成完整回應
        
        Args:
            query: 用戶查詢
            
        Returns:
            完整回應
        """
        try:
            if self.verbose:
                print(f"[_generate_complete_response] 開始生成完整回應...")
            
            # 獲取旅宿推薦結果
            hotel_recommendation = self.recall("hotel_recommendation")
            if self.verbose:
                if hotel_recommendation:
                    print(f"[_generate_complete_response] 找到旅宿推薦結果，狀態: {hotel_recommendation.get('status', 'unknown')}")
                else:
                    print(f"[_generate_complete_response] 未找到旅宿推薦結果")
            
            # 組合回應
            response = ""
            
            if hotel_recommendation:
                hotel_data = hotel_recommendation.get("data", {})
                hotel_recommendation_text = hotel_data.get("recommendation", "")
                if hotel_recommendation_text:
                    response += f"{hotel_recommendation_text}\n\n"
                    if self.verbose:
                        print(f"[_generate_complete_response] 添加旅宿推薦文本: {hotel_recommendation_text[:50]}...")
            
            if not response:
                # 如果沒有特定的推薦或規劃結果，生成一個通用回應
                response = "感謝您的查詢。我是您的旅遊助手，可以幫您推薦旅宿和規劃行程。請告訴我您的旅遊需求，例如目的地、日期、人數和預算等，我會為您提供最適合的建議。"
                if self.verbose:
                    print(f"[_generate_complete_response] 使用通用回應")
            
            if self.verbose:
                print(f"[_generate_complete_response] 完整回應生成完成: {response[:50]}...")
            
            return response
        except Exception as e:
            if self.verbose:
                print(f"[_generate_complete_response] 生成完整回應時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
            return "抱歉，我在處理您的請求時遇到了問題。請稍後再試或重新描述您的需求。"
    
    def _get_hotel_agent(self) -> Optional[BaseAgent]:
        """
        獲取旅宿推薦 Agent
        
        Returns:
            旅宿推薦 Agent 或 None
        """
        # 從協作者列表中查找旅宿推薦 Agent
        for agent in self.collaborators:
            if "hotel" in agent.role.lower() or "旅宿" in agent.role:
                return agent
        return None
    
    def _get_itinerary_agent(self) -> Optional[BaseAgent]:
        """
        獲取行程規劃 Agent
        
        Returns:
            行程規劃 Agent 或 None
        """
        # 從協作者列表中查找行程規劃 Agent
        for agent in self.collaborators:
            if "itinerary" in agent.role.lower() or "行程" in agent.role:
                return agent
        return None
    
    def clear_conversation(self) -> None:
        """
        清除對話歷史
        """
        self.conversation_history = []
        if self.verbose:
            print(f"{self.name} 清除了對話歷史")
            
    def chat(self, message: str) -> Dict[str, Any]:
        """
        與用戶對話的便捷方法
        
        Args:
            message: 用戶消息
            
        Returns:
            回應結果
        """
        task = {
            "query": message,
            "timestamp": time.time()
        }
        return self.execute_task(task) 