from typing import Dict, List, Any, Optional
import time
import openai
import os
from .base_agent import BaseAgent

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
        
        # 添加到對話歷史
        self.conversation_history.append({"role": "user", "content": user_query})
        
        # 生成快速回應 (5秒內)
        quick_response = self._generate_quick_response(user_query)
        
        # 更新進度
        self.task_progress = 0.3
        
        # 檢查是否需要協調其他 Agent
        if self._needs_hotel_recommendation(user_query):
            # 如果有旅宿推薦 Agent，則協調它
            hotel_agent = self._get_hotel_agent()
            if hotel_agent:
                hotel_task = {
                    "query": user_query,
                    "type": "hotel_recommendation",
                    "parameters": self._extract_hotel_parameters(user_query)
                }
                hotel_result = self.collaborate(hotel_agent, hotel_task)
                self.remember("hotel_recommendation", hotel_result)
        
        # 更新進度
        self.task_progress = 0.6
        
        if self._needs_itinerary_planning(user_query):
            # 如果有行程規劃 Agent，則協調它
            itinerary_agent = self._get_itinerary_agent()
            if itinerary_agent:
                itinerary_task = {
                    "query": user_query,
                    "type": "itinerary_planning",
                    "parameters": self._extract_itinerary_parameters(user_query)
                }
                itinerary_result = self.collaborate(itinerary_agent, itinerary_task)
                self.remember("itinerary_planning", itinerary_result)
        
        # 更新進度
        self.task_progress = 0.9
        
        # 生成完整回應
        complete_response = self._generate_complete_response(user_query)
        
        # 添加到對話歷史
        self.conversation_history.append({"role": "assistant", "content": complete_response})
        
        # 更新任務狀態
        self.task_status = "completed"
        self.task_progress = 1.0
        self.task_result = {
            "quick_response": quick_response,
            "complete_response": complete_response,
            "processing_time": time.time() - start_time
        }
        
        return self.task_result
    
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
    
    def _generate_quick_response(self, query: str) -> str:
        """
        生成快速回應 (5秒內)
        
        Args:
            query: 用戶查詢
            
        Returns:
            快速回應文本
        """
        try:
            # 使用 OpenAI API 生成快速回應
            system_prompt = """
            你是一個旅遊助手，負責快速回應用戶的旅遊查詢。
            你需要在5秒內給出初步回應，表明你已理解用戶的需求，並正在準備更詳細的信息。
            不要在這個階段提供具體的旅宿推薦或行程規劃，只需確認你理解了用戶的需求。
            """
            
            response = openai.chat.completions.create(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            if self.verbose:
                print(f"生成快速回應時出錯: {e}")
            return "我已收到您的查詢，正在為您準備回應..."
    
    def _generate_complete_response(self, query: str) -> str:
        """
        生成完整回應
        
        Args:
            query: 用戶查詢
            
        Returns:
            完整回應文本
        """
        try:
            # 準備上下文信息
            context = ""
            
            # 添加旅宿推薦信息（如果有）
            hotel_recommendation = self.recall("hotel_recommendation")
            if hotel_recommendation:
                context += f"\n旅宿推薦信息: {hotel_recommendation}\n"
            
            # 添加行程規劃信息（如果有）
            itinerary_planning = self.recall("itinerary_planning")
            if itinerary_planning:
                context += f"\n行程規劃信息: {itinerary_planning}\n"
            
            # 使用 OpenAI API 生成完整回應
            system_prompt = f"""
            你是一個旅遊助手，負責為用戶提供旅遊建議。
            基於以下信息，為用戶提供完整的旅遊解決方案，包括旅宿推薦和行程規劃。
            
            上下文信息:
            {context}
            
            請提供一個結構清晰、信息豐富的回應，包括:
            1. 推薦的住宿選項（如果適用）
            2. 周邊景點安排（如果適用）
            3. 交通建議（如果適用）
            
            回應應該友好、專業，並針對用戶的具體需求。
            """
            
            # 構建對話歷史
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加最近的對話歷史（最多5輪）
            recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
            for msg in recent_history:
                if msg["role"] != "system":  # 排除系統消息
                    messages.append(msg)
            
            # 添加當前查詢
            messages.append({"role": "user", "content": query})
            
            response = openai.chat.completions.create(
                model=self.llm,
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            if self.verbose:
                print(f"生成完整回應時出錯: {e}")
            return "抱歉，我在處理您的請求時遇到了問題。請稍後再試或重新描述您的需求。"
    
    def _needs_hotel_recommendation(self, query: str) -> bool:
        """
        判斷是否需要旅宿推薦
        
        Args:
            query: 用戶查詢
            
        Returns:
            是否需要旅宿推薦
        """
        # 簡單的關鍵詞匹配，實際應用中可以使用更複雜的NLP方法
        hotel_keywords = ["旅館", "飯店", "住宿", "旅宿", "民宿", "酒店", "住哪", "住哪裡", "哪裡住"]
        return any(keyword in query for keyword in hotel_keywords)
    
    def _needs_itinerary_planning(self, query: str) -> bool:
        """
        判斷是否需要行程規劃
        
        Args:
            query: 用戶查詢
            
        Returns:
            是否需要行程規劃
        """
        # 簡單的關鍵詞匹配，實際應用中可以使用更複雜的NLP方法
        itinerary_keywords = ["行程", "景點", "玩什麼", "去哪", "去哪裡", "遊玩", "活動", "規劃", "安排"]
        return any(keyword in query for keyword in itinerary_keywords)
    
    def _extract_hotel_parameters(self, query: str) -> Dict[str, Any]:
        """
        從用戶查詢中提取旅宿參數
        
        Args:
            query: 用戶查詢
            
        Returns:
            旅宿參數字典
        """
        # 實際應用中應使用 NLP 或 LLM 提取參數
        # 這裡僅作為示例
        return {
            "location": None,  # 地點
            "check_in": None,  # 入住日期
            "check_out": None,  # 退房日期
            "guests": None,  # 人數
            "budget": None,  # 預算
            "preferences": []  # 偏好
        }
    
    def _extract_itinerary_parameters(self, query: str) -> Dict[str, Any]:
        """
        從用戶查詢中提取行程參數
        
        Args:
            query: 用戶查詢
            
        Returns:
            行程參數字典
        """
        # 實際應用中應使用 NLP 或 LLM 提取參數
        # 這裡僅作為示例
        return {
            "location": None,  # 地點
            "duration": None,  # 行程天數
            "interests": [],  # 興趣
            "transportation": None,  # 交通方式
            "with_children": None  # 是否有兒童
        }
    
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