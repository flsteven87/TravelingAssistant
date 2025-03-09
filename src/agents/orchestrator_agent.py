from typing import Dict, List, Any, Optional
import time
import openai
import os
import json
from pydantic import BaseModel, Field
from .base_agent import BaseAgent

# 定義 Pydantic 模型用於結構化輸出
class UserIntentAnalysis(BaseModel):
    """分析用戶意圖的查詢參數"""
    query: str = Field(..., description="用戶的查詢文本")
    needs_hotel_recommendation: bool = Field(description="用戶是否需要旅宿推薦")
    needs_itinerary_planning: bool = Field(description="用戶是否需要行程規劃")
    explanation: str = Field(description="分析結果的解釋")

class HotelParameters(BaseModel):
    """從用戶查詢中提取旅宿參數"""
    query: str = Field(..., description="用戶的查詢文本")
    location: Optional[str] = Field(description="目的地，如縣市名稱")
    check_in_date: Optional[str] = Field(description="入住日期，格式為 YYYY-MM-DD")
    check_out_date: Optional[str] = Field(description="退房日期，格式為 YYYY-MM-DD")
    adults: Optional[int] = Field(description="成人人數")
    children: Optional[int] = Field(description="兒童人數")
    budget_min: Optional[int] = Field(description="最低預算（每晚）")
    budget_max: Optional[int] = Field(description="最高預算（每晚）")
    hotel_types: Optional[List[str]] = Field(description="偏好的旅館類型")
    facilities: Optional[List[str]] = Field(description="偏好的設施")
    special_requirements: Optional[str] = Field(description="特殊需求")

class ItineraryParameters(BaseModel):
    """從用戶查詢中提取行程參數"""
    query: str = Field(..., description="用戶的查詢文本")
    location: Optional[str] = Field(description="目的地，如縣市名稱")
    start_date: Optional[str] = Field(description="開始日期，格式為 YYYY-MM-DD")
    end_date: Optional[str] = Field(description="結束日期，格式為 YYYY-MM-DD")
    duration: Optional[int] = Field(description="行程天數")
    interests: Optional[List[str]] = Field(description="興趣愛好")
    transportation: Optional[str] = Field(description="交通方式")
    with_children: Optional[bool] = Field(description="是否有兒童")
    budget: Optional[str] = Field(description="預算範圍")

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
        super().__init__(name, role, goal, backstory, description, **kwargs)
        
        # 初始化 OpenAI 客戶端
        openai.api_key = self.api_key
        
        # 用戶對話歷史 - 確保這個屬性被正確初始化
        self.conversation_history = []
        
        # 初始化任務狀態
        self.current_task = None
        self.task_status = "idle"
        self.task_progress = 0.0
        self.task_result = None
        
        # 設置 LLM 模型
        self.llm = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        # 設置快速回應時間限制 (5秒)
        self.quick_response_time = 5
        
        # 完整回應時間限制 (30秒)
        self.complete_response_time = 30
        
        if self.verbose:
            print(f"[OrchestratorAgent] 初始化完成，對話歷史已創建")
    
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
        
        # 確保 conversation_history 存在
        if not hasattr(self, 'conversation_history'):
            self.conversation_history = []
        
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
        execution_time = end_time - start_time
        
        if self.verbose:
            print(f"[OrchestratorAgent] 任務完成，執行時間: {execution_time:.2f}秒")
        
        # 設置任務結果
        self.task_result = {
            "quick_response": quick_response,
            "complete_response": complete_response,
            "execution_time": execution_time
        }
        
        # 返回結果
        return {
            "quick_response": quick_response,
            "complete_response": complete_response,
            "execution_time": execution_time
        }
    
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
            
            如果用戶提到了住宿、飯店、旅館等相關詞彙，或者詢問住哪裡，則 needs_hotel_recommendation 應為 true。
            如果用戶提到了行程、景點、活動等相關詞彙，或者詢問去哪裡玩，則 needs_itinerary_planning 應為 true。
            """
            
            if self.verbose:
                print(f"[_analyze_user_intent] 調用 OpenAI API...")
            
            # 使用 OpenAI 的 parse 方法
            client = openai.OpenAI(api_key=self.api_key)
            completion = client.beta.chat.completions.parse(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format=UserIntentAnalysis,
                temperature=0.1,
                max_tokens=1000
            )
            
            # 獲取解析後的結果
            result = completion.choices[0].message.parsed
            
            if self.verbose:
                print(f"[_analyze_user_intent] 分析結果: {result}")
            
            # 如果用戶提到了旅館、飯店等，但 needs_hotel_recommendation 為 False，則修正
            if not result.needs_hotel_recommendation:
                hotel_keywords = ["旅館", "飯店", "住宿", "旅宿", "民宿", "酒店", "住哪", "住哪裡", "哪裡住"]
                if any(keyword in query for keyword in hotel_keywords):
                    result.needs_hotel_recommendation = True
                    if self.verbose:
                        print(f"[_analyze_user_intent] 修正 needs_hotel_recommendation 為 True，因為檢測到旅宿關鍵詞")
            
            # 如果用戶提到了行程、景點等，但 needs_itinerary_planning 為 False，則修正
            if not result.needs_itinerary_planning:
                itinerary_keywords = ["行程", "景點", "玩什麼", "去哪", "去哪裡", "遊玩", "活動", "規劃", "安排"]
                if any(keyword in query for keyword in itinerary_keywords):
                    result.needs_itinerary_planning = True
                    if self.verbose:
                        print(f"[_analyze_user_intent] 修正 needs_itinerary_planning 為 True，因為檢測到行程關鍵詞")
            
            # 將 Pydantic 模型轉換為字典
            return result.model_dump()
        except Exception as e:
            if self.verbose:
                print(f"[_analyze_user_intent] 分析用戶意圖時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
            
            # 重新拋出異常，不使用備用方案
            raise
    
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
            
            # 使用 OpenAI 的 parse 方法
            client = openai.OpenAI()
            completion = client.beta.chat.completions.parse(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format=HotelParameters,
                temperature=0.1,
                max_tokens=1000
            )
            
            # 獲取解析後的結果
            result = completion.choices[0].message.parsed
            
            if self.verbose:
                print(f"[_extract_hotel_parameters_llm] 提取結果: {result}")
            
            # 將 Pydantic 模型轉換為字典
            return result.model_dump()
        except Exception as e:
            if self.verbose:
                print(f"[_extract_hotel_parameters_llm] 提取旅宿參數時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
            
            # 重新拋出異常，不使用備用方案
            raise
    
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
            
            # 使用 OpenAI 的 parse 方法
            client = openai.OpenAI()
            completion = client.beta.chat.completions.parse(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format=ItineraryParameters,
                temperature=0.1,
                max_tokens=1000
            )
            
            # 獲取解析後的結果
            result = completion.choices[0].message.parsed
            
            if self.verbose:
                print(f"[_extract_itinerary_parameters_llm] 提取結果: {result}")
            
            # 將 Pydantic 模型轉換為字典
            return result.model_dump()
        except Exception as e:
            if self.verbose:
                print(f"[_extract_itinerary_parameters_llm] 提取行程參數時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
            
            # 重新拋出異常，不使用備用方案
            raise
    
    def _generate_quick_response(self, query: str) -> str:
        """
        生成快速回應
        
        Args:
            query: 用戶查詢
            
        Returns:
            快速回應
        """
        try:
            if self.verbose:
                print(f"[_generate_quick_response] 開始生成快速回應...")
            
            # 分析用戶意圖
            intent_analysis = self._analyze_user_intent(query)
            
            if self.verbose:
                print(f"[_generate_quick_response] 用戶意圖分析結果: {intent_analysis}")
            
            if intent_analysis.get("needs_hotel_recommendation", False):
                if self.verbose:
                    print(f"[_generate_quick_response] 用戶需要旅宿推薦")
                return "我正在為您尋找合適的旅宿選擇，請稍候..."
            elif intent_analysis.get("needs_itinerary_planning", False):
                if self.verbose:
                    print(f"[_generate_quick_response] 用戶需要行程規劃")
                return "我正在為您規劃行程，請稍候..."
            else:
                if self.verbose:
                    print(f"[_generate_quick_response] 無法確定用戶意圖，使用通用回應")
                return "我正在處理您的請求，請稍候..."
        except Exception as e:
            if self.verbose:
                print(f"[_generate_quick_response] 生成快速回應時發生錯誤: {str(e)}")
                import traceback
                print(traceback.format_exc())
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
                hotel_recommendation_text = hotel_data.get("complete_response", "")
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
            return "抱歉，我在處理您的請求時遇到了問題。請稍後再試或換一種方式提問。"
    
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
        # 確保 conversation_history 存在，如果不存在則創建
        if not hasattr(self, 'conversation_history'):
            self.conversation_history = []
        else:
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
        # 確保 conversation_history 存在
        if not hasattr(self, 'conversation_history'):
            self.conversation_history = []
        
        task = {
            "query": message,
            "timestamp": time.time()
        }
        
        # 執行任務並返回結果
        result = self.execute_task(task)
        return result 