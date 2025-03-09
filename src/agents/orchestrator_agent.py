from typing import Dict, List, Any, Optional
import time
import openai
import os
import json
from pydantic import BaseModel, Field
from .base_agent import BaseAgent
import logging
from ..utils import logging_utils

# 定義 Pydantic 模型用於結構化輸出
class UserIntentAnalysis(BaseModel):
    """分析用戶意圖的查詢參數"""
    query: str = Field(..., description="用戶的查詢文本")
    needs_hotel_recommendation: bool = Field(description="用戶是否需要旅宿推薦")
    needs_itinerary_planning: bool = Field(description="用戶是否需要行程規劃")
    explanation: str = Field(description="分析結果的解釋")

class TaskParameters(BaseModel):
    """從用戶查詢中提取任務參數的基類"""
    query: str = Field(..., description="用戶的查詢文本")
    location: Optional[str] = Field(None, description="目的地，如縣市名稱")

class HotelParameters(TaskParameters):
    """從用戶查詢中提取旅宿參數"""
    check_in_date: Optional[str] = Field(None, description="入住日期，格式為 YYYY-MM-DD")
    check_out_date: Optional[str] = Field(None, description="退房日期，格式為 YYYY-MM-DD")
    adults: Optional[int] = Field(None, description="成人人數")
    children: Optional[int] = Field(None, description="兒童人數")
    budget_min: Optional[int] = Field(None, description="最低預算（每晚）")
    budget_max: Optional[int] = Field(None, description="最高預算（每晚）")
    hotel_types: Optional[List[str]] = Field(None, description="偏好的旅館類型")
    facilities: Optional[List[str]] = Field(None, description="偏好的設施")
    special_requirements: Optional[str] = Field(None, description="特殊需求")

class ItineraryParameters(TaskParameters):
    """從用戶查詢中提取行程參數"""
    start_date: Optional[str] = Field(None, description="開始日期，格式為 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="結束日期，格式為 YYYY-MM-DD")
    duration: Optional[int] = Field(None, description="行程天數")
    interests: Optional[List[str]] = Field(None, description="興趣愛好")
    transportation: Optional[str] = Field(None, description="交通方式")
    with_children: Optional[bool] = Field(None, description="是否有兒童")
    budget: Optional[str] = Field(None, description="預算範圍")

class CoordinationStrategy(BaseModel):
    """協調策略"""
    query: str = Field(..., description="用戶的查詢文本")
    needs_hotel_agent: bool = Field(description="是否需要旅宿推薦 Agent")
    needs_itinerary_agent: bool = Field(description="是否需要行程規劃 Agent")
    quick_response: str = Field(description="快速回應內容")
    coordination_plan: str = Field(description="協調計劃的詳細說明")

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
        
        # 用戶對話歷史
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
        
        # 初始化日誌
        self.logger = logging_utils.setup_logger(
            name=self.name,
            level="info",
            verbose=self.verbose
        )
        
        logging_utils.info(self.logger, "初始化完成，對話歷史已創建")
    
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
        
        logging_utils.info(self.logger, f"開始執行任務: {user_query[:50]}...", "execute_task")
        
        # 添加到對話歷史
        self.conversation_history.append({"role": "user", "content": user_query})
        
        try:
            # 使用 LLM 制定協調策略
            logging_utils.info(self.logger, "制定協調策略...", "execute_task")
            
            coordination_strategy = self._create_coordination_strategy(user_query)
            
            logging_utils.info(self.logger, f"協調策略: {coordination_strategy}", "execute_task")
            
            # 獲取快速回應
            quick_response = coordination_strategy.get("quick_response", "我正在處理您的請求，請稍候...")
            
            # 更新進度
            self.task_progress = 0.3
            
            # 根據協調策略協調不同的 Agent
            hotel_result = None
            itinerary_result = None
            
            if coordination_strategy.get("needs_hotel_agent", False):
                # 提取旅宿參數
                logging_utils.info(self.logger, "提取旅宿參數...", "execute_task")
                
                hotel_params = self._extract_parameters(user_query, "hotel")
                
                logging_utils.info(self.logger, f"旅宿參數: {hotel_params}", "execute_task")
                
                # 如果有旅宿推薦 Agent，則協調它
                hotel_agent = self._get_hotel_agent()
                if hotel_agent:
                    logging_utils.info(self.logger, f"找到旅宿推薦 Agent: {hotel_agent.name}", "execute_task")
                    
                    hotel_task = {
                        "query": user_query,
                        "type": "hotel_recommendation",
                        "parameters": hotel_params
                    }
                    
                    logging_utils.info(self.logger, "委派任務給旅宿推薦 Agent...", "execute_task")
                    
                    hotel_result = self.collaborate(hotel_agent, hotel_task)
                    
                    logging_utils.info(self.logger, f"旅宿推薦結果狀態: {hotel_result.get('status', 'unknown')}", "execute_task")
                    
                    self.remember("hotel_recommendation", hotel_result)
            
            if coordination_strategy.get("needs_itinerary_agent", False):
                # 提取行程參數
                logging_utils.info(self.logger, "提取行程參數...", "execute_task")
                
                itinerary_params = self._extract_parameters(user_query, "itinerary")
                
                logging_utils.info(self.logger, f"行程參數: {itinerary_params}", "execute_task")
                
                # 如果有行程規劃 Agent，則協調它
                itinerary_agent = self._get_itinerary_agent()
                if itinerary_agent:
                    logging_utils.info(self.logger, f"找到行程規劃 Agent: {itinerary_agent.name}", "execute_task")
                    
                    itinerary_task = {
                        "query": user_query,
                        "type": "itinerary_planning",
                        "parameters": itinerary_params
                    }
                    
                    logging_utils.info(self.logger, "委派任務給行程規劃 Agent...", "execute_task")
                    
                    itinerary_result = self.collaborate(itinerary_agent, itinerary_task)
                    
                    logging_utils.info(self.logger, f"行程規劃結果狀態: {itinerary_result.get('status', 'unknown')}", "execute_task")
                    
                    self.remember("itinerary_planning", itinerary_result)
            
            # 更新進度
            self.task_progress = 0.6
            
            # 生成完整回應
            logging_utils.info(self.logger, "生成完整回應...", "execute_task")
            
            complete_response = self._generate_complete_response(user_query, hotel_result, itinerary_result)
            
            logging_utils.info(self.logger, f"完整回應: {complete_response[:100]}...", "execute_task")
            
            # 更新進度
            self.task_progress = 1.0
            
            # 更新任務狀態
            self.task_status = "completed"
            
            # 記錄任務結束時間
            end_time = time.time()
            execution_time = end_time - start_time
            
            logging_utils.info(self.logger, f"任務完成，執行時間: {execution_time:.2f}秒", "execute_task")
            
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
        
        except Exception as e:
            logging_utils.log_exception(self.logger, e, "execute_task")
            
            # 返回錯誤結果
            return {
                "quick_response": "抱歉，我在處理您的請求時遇到了問題。",
                "complete_response": f"抱歉，我在處理您的請求時遇到了技術問題。錯誤信息: {str(e)}。請稍後再試或者換一種方式提問。",
                "execution_time": time.time() - start_time
            }
    
    def _create_coordination_strategy(self, query: str) -> Dict[str, Any]:
        """
        使用 LLM 制定協調策略
        
        Args:
            query: 用戶查詢
            
        Returns:
            協調策略
        """
        try:
            logging_utils.info(self.logger, "開始制定協調策略...", "_create_coordination_strategy")
            
            # 準備系統提示詞
            system_prompt = f"""
            你是 {self.name}，一個 {self.role}。
            
            你的任務是分析用戶的查詢，制定協調策略，決定是否需要旅宿推薦 Agent 或行程規劃 Agent 的協助。
            
            旅宿推薦相關的內容包括：住宿選擇、旅館推薦、飯店比較、民宿查詢、住宿預算、旅宿設施等。
            行程規劃相關的內容包括：景點推薦、行程安排、活動建議、交通規劃、遊玩路線、時間分配等。
            
            請仔細分析用戶的查詢，判斷用戶的真實意圖，並提供一個合適的快速回應和協調計劃。
            """
            
            logging_utils.info(self.logger, "調用 OpenAI API...", "_create_coordination_strategy")
            
            # 使用 OpenAI 的 parse 方法
            client = openai.OpenAI(api_key=self.api_key)
            completion = client.beta.chat.completions.parse(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format=CoordinationStrategy,
                temperature=0.1,
                max_tokens=1000
            )
            
            # 獲取解析後的結果
            result = completion.choices[0].message.parsed
            
            logging_utils.info(self.logger, f"協調策略: {result}", "_create_coordination_strategy")
            
            # 將 Pydantic 模型轉換為字典
            return result.model_dump()
        
        except Exception as e:
            logging_utils.log_exception(self.logger, e, "_create_coordination_strategy")
            
            # 返回默認策略
            return {
                "query": query,
                "needs_hotel_agent": True,  # 默認假設需要旅宿推薦
                "needs_itinerary_agent": True,  # 默認假設需要行程規劃
                "quick_response": "我正在處理您的請求，請稍候...",
                "coordination_plan": "由於無法確定用戶的具體需求，將同時協調旅宿推薦和行程規劃 Agent。"
            }
    
    def _extract_parameters(self, query: str, param_type: str) -> Dict[str, Any]:
        """
        使用 LLM 從用戶查詢中提取參數
        
        Args:
            query: 用戶查詢
            param_type: 參數類型，'hotel' 或 'itinerary'
            
        Returns:
            參數字典
        """
        try:
            logging_utils.info(self.logger, f"開始提取 {param_type} 參數...", "_extract_parameters")
            
            # 準備系統提示詞
            system_prompt = f"""
            你是 {self.name}，一個 {self.role}。
            
            你的任務是從用戶的查詢中提取 {param_type} 相關的參數。
            """
            
            if param_type == "hotel":
                system_prompt += """
                請提取以下參數：
                - 目的地（縣市名稱）
                - 入住日期和退房日期
                - 成人和兒童人數
                - 預算範圍
                - 偏好的旅館類型
                - 偏好的設施
                - 特殊需求
                
                如果用戶沒有明確提供某些參數，請將對應的值設為 null。
                """
                response_format = HotelParameters
            else:  # itinerary
                system_prompt += """
                請提取以下參數：
                - 目的地（縣市名稱）
                - 開始日期和結束日期
                - 行程天數
                - 興趣愛好
                - 交通方式
                - 是否有兒童
                - 預算範圍
                
                如果用戶沒有明確提供某些參數，請將對應的值設為 null。
                """
                response_format = ItineraryParameters
            
            logging_utils.info(self.logger, "調用 OpenAI API...", "_extract_parameters")
            
            # 使用 OpenAI 的 parse 方法
            client = openai.OpenAI(api_key=self.api_key)
            completion = client.beta.chat.completions.parse(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format=response_format,
                temperature=0.1,
                max_tokens=1000
            )
            
            # 獲取解析後的結果
            result = completion.choices[0].message.parsed
            
            logging_utils.info(self.logger, f"提取結果: {result}", "_extract_parameters")
            
            # 將 Pydantic 模型轉換為字典
            return result.model_dump()
        
        except Exception as e:
            logging_utils.log_exception(self.logger, e, "_extract_parameters")
            
            # 返回只包含查詢的基本參數
            return {"query": query}
    
    def _generate_complete_response(self, query: str, hotel_result: Optional[Dict[str, Any]] = None, itinerary_result: Optional[Dict[str, Any]] = None) -> str:
        """
        生成完整回應
        
        Args:
            query: 用戶查詢
            hotel_result: 旅宿推薦結果
            itinerary_result: 行程規劃結果
            
        Returns:
            完整回應
        """
        try:
            logging_utils.info(self.logger, "開始生成完整回應...", "_generate_complete_response")
            
            # 準備系統提示詞
            system_prompt = f"""
            你是 {self.name}，一個 {self.role}。
            
            你的任務是根據用戶的查詢和專業 Agent 的結果，生成一個完整的回應。
            
            請確保回應是連貫的、有幫助的，並且涵蓋用戶查詢的所有方面。
            如果某些信息缺失，請坦誠地告知用戶，並提供可行的下一步建議。
            """
            
            # 準備用戶提示詞
            user_prompt = f"用戶查詢: {query}\n\n"
            
            if hotel_result:
                hotel_data = hotel_result.get("data", {})
                hotel_response = hotel_data.get("complete_response", "")
                if hotel_response:
                    user_prompt += f"旅宿推薦結果:\n{hotel_response}\n\n"
            
            if itinerary_result:
                itinerary_data = itinerary_result.get("data", {})
                itinerary_response = itinerary_data.get("complete_response", "")
                if itinerary_response:
                    user_prompt += f"行程規劃結果:\n{itinerary_response}\n\n"
            
            user_prompt += "請根據以上信息，生成一個完整的回應。"
            
            logging_utils.info(self.logger, "調用 OpenAI API...", "_generate_complete_response")
            
            # 使用 OpenAI 的 chat completions
            client = openai.OpenAI(api_key=self.api_key)
            completion = client.chat.completions.create(
                model=self.llm,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # 獲取回應
            response = completion.choices[0].message.content
            
            logging_utils.info(self.logger, f"完整回應: {response[:100]}...", "_generate_complete_response")
            
            return response
        
        except Exception as e:
            logging_utils.log_exception(self.logger, e, "_generate_complete_response")
            
            # 如果有旅宿推薦或行程規劃結果，直接返回
            if hotel_result and "data" in hotel_result and "complete_response" in hotel_result["data"]:
                return hotel_result["data"]["complete_response"]
            
            if itinerary_result and "data" in itinerary_result and "complete_response" in itinerary_result["data"]:
                return itinerary_result["data"]["complete_response"]
            
            # 否則返回通用回應
            return "感謝您的查詢。我是您的旅遊助手，可以幫您推薦旅宿和規劃行程。請告訴我您的旅遊需求，例如目的地、日期、人數和預算等，我會為您提供最適合的建議。"
    
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
        
        logging_utils.info(self.logger, "清除了對話歷史", "clear_conversation")
            
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
        
        # 執行任務並返回結果
        result = self.execute_task(task)
        return result 