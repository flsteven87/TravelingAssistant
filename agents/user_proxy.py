"""
User proxy agent for handling user interactions.
"""
from datetime import datetime
import sys
import os
import logging
import streamlit as st
import asyncio

# Add parent directory to path to allow module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autogen_agentchat.agents import UserProxyAgent

# 設置日誌
logger = logging.getLogger('traveling_assistant.user_proxy')

class TravelUserProxyAgent(UserProxyAgent):
    """
    A user proxy agent that interacts with the multi-agent travel recommendation system.
    This agent handles user input, displays responses, and manages the user experience.
    """
    
    def __init__(self, name="User Proxy", **kwargs):
        super().__init__(name=name, **kwargs)
        self.user_preferences = {}
        self.last_response_time = None
        self.received_initial_response = False
        self.received_complete_response = False
        self.logger = logging.getLogger('traveling_assistant.user_proxy')
    
    def get_user_input(self, prompt=None):
        """Get user input for travel preferences."""
        if prompt:
            print(prompt)
        
        return input("請輸入您的回應: ")
    
    def process_user_query(self, message):
        """
        Process the user's initial query to extract travel preferences.
        Returns a structured query with the extracted preferences.
        """
        if isinstance(message, str):
            content = message
        else:
            # For v0.4 compatibility, the message might be a ChatMessage
            content = message.content if hasattr(message, "content") else str(message)
        
        # Default preferences structure
        preferences = {
            "destination": None,
            "date_range": None,
            "num_people": None,
            "budget": None,
            "interests": [],
            "hotel_preferences": {},
            "other_requirements": None
        }
        
        # Extract destination (very simplified)
        if "台北" in content:
            preferences["destination"] = "台北市"
        elif "高雄" in content:
            preferences["destination"] = "高雄市"
        
        # Extract date range (simplified)
        # In practice, you'd use regex patterns or NLP for date extraction
        if "明天" in content:
            from datetime import datetime, timedelta
            tomorrow = datetime.now() + timedelta(days=1)
            day_after = tomorrow + timedelta(days=1)
            preferences["date_range"] = {
                "start": tomorrow.strftime("%Y-%m-%d"),
                "end": day_after.strftime("%Y-%m-%d")
            }
        
        # Extract number of people
        import re
        people_matches = re.findall(r'(\d+)人', content)
        if people_matches:
            preferences["num_people"] = int(people_matches[0])
        
        # Extract budget
        budget_matches = re.findall(r'預算(\d+)', content)
        if budget_matches:
            preferences["budget"] = int(budget_matches[0])
        
        # Extract interests
        for interest in ["美食", "購物", "歷史", "文化", "自然", "藝術"]:
            if interest in content:
                preferences["interests"].append(interest)
        
        # Store the extracted preferences
        self.user_preferences = preferences
        
        return preferences
    
    async def receive_response(self, response, is_initial=False, is_complete=False):
        """
        Handle responses from the coordinator and update the UI.
        This method is called by the coordinator agent to provide responses.
        """
        self.logger.info(f"Received {'initial' if is_initial else 'complete' if is_complete else 'partial'} response")
        self.logger.info(f"Response content: {response[:50]}...")
        
        # Update UI via callback if set
        if self.update_callback:
            self.logger.info("Using update callback to send response to UI")
            self.update_callback(response)
        else:
            # Fallback to session_state directly (less preferred)
            self.logger.warning("No update callback set, using session_state directly")
            st.session_state.current_response = response
        
        # If this is the complete response, mark processing as done
        if is_complete:
            self.logger.info("Received complete response, marking processing as done")
            st.session_state.processing = False
        
        return response
    
    async def get_human_input(self, prompt=None):
        """Override the default get_human_input to provide UI enhancements."""
        if prompt:
            print(prompt)
        
        return self.get_user_input("請告訴我您的旅遊需求: ")


def create_user_proxy_agent(model_client=None):
    """Factory function to create and configure a user proxy agent."""
    return TravelUserProxyAgent(
        name="user_proxy"
    ) 


class StreamlitUserProxyAgent:
    """
    Streamlit-specific user proxy agent for the Traveling Assistant.
    Manages user interactions via the Streamlit UI.
    """
    
    def __init__(self, name="user_proxy"):
        """Initialize the Streamlit user proxy agent."""
        self.name = name
        self.coordinator = None
        self.user_preferences = {}
        self.logger = logging.getLogger('traveling_assistant.streamlit_user_proxy')
        self.update_callback = None
    
    def set_coordinator(self, coordinator):
        """Set the coordinator agent for this user proxy."""
        self.coordinator = coordinator
        self.logger.info(f"設置協調器: {coordinator.name}")
        
    def set_update_callback(self, callback):
        """Set a callback function for updating the UI during response generation."""
        self.update_callback = callback
    
    def process_user_query(self, message):
        """
        Process the user's query to extract travel preferences.
        Returns a structured dictionary with the extracted preferences.
        """
        if isinstance(message, str):
            content = message
        else:
            # 兼容不同類型的消息對象
            content = message.content if hasattr(message, "content") else str(message)
        
        # 默認偏好結構
        preferences = {
            "destination": None,
            "date_range": None,
            "num_people": None,
            "budget": None,
            "interests": [],
            "hotel_preferences": {},
            "other_requirements": None
        }
        
        # 提取目的地
        if "台北" in content:
            preferences["destination"] = "台北市"
        elif "高雄" in content:
            preferences["destination"] = "高雄市"
        elif "花蓮" in content:
            preferences["destination"] = "花蓮縣"
        elif "台南" in content:
            preferences["destination"] = "台南市"
        elif "台中" in content:
            preferences["destination"] = "台中市"
        
        # 提取日期範圍
        import re
        from datetime import datetime, timedelta
        
        # 檢查特定日期
        if "明天" in content:
            tomorrow = datetime.now() + timedelta(days=1)
            day_after = tomorrow + timedelta(days=1)
            preferences["date_range"] = {
                "start": tomorrow.strftime("%Y-%m-%d"),
                "end": day_after.strftime("%Y-%m-%d")
            }
        elif "下週" in content or "下星期" in content:
            next_week = datetime.now() + timedelta(days=7)
            end_next_week = next_week + timedelta(days=3)  # 默認3天行程
            preferences["date_range"] = {
                "start": next_week.strftime("%Y-%m-%d"),
                "end": end_next_week.strftime("%Y-%m-%d")
            }
        elif "下個月" in content:
            next_month = datetime.now() + timedelta(days=30)
            end_next_month = next_month + timedelta(days=3)  # 默認3天行程
            preferences["date_range"] = {
                "start": next_month.strftime("%Y-%m-%d"),
                "end": end_next_month.strftime("%Y-%m-%d")
            }
        
        # 提取行程天數
        day_matches = re.findall(r'(\d+)[天日]', content)
        if day_matches:
            days = int(day_matches[0])
            # 如果有開始日期但沒有結束日期
            if preferences.get("date_range") and preferences["date_range"].get("start"):
                start_date = datetime.strptime(preferences["date_range"]["start"], "%Y-%m-%d")
                end_date = start_date + timedelta(days=days)
                preferences["date_range"]["end"] = end_date.strftime("%Y-%m-%d")
        
        # 提取人數
        people_matches = re.findall(r'(\d+)人', content)
        if people_matches:
            preferences["num_people"] = int(people_matches[0])
        
        # 家庭標誌
        if "家人" in content or "家庭" in content:
            if not preferences.get("num_people"):
                preferences["num_people"] = 3  # 默認家庭人數
            preferences["hotel_preferences"]["family_friendly"] = True
        
        # 兒童標誌
        if "小孩" in content or "孩子" in content or "兒童" in content:
            preferences["hotel_preferences"]["family_friendly"] = True
            preferences["hotel_preferences"]["has_children"] = True
        
        # 提取成人/兒童數量
        adult_matches = re.findall(r'(\d+)大', content)
        child_matches = re.findall(r'(\d+)小', content)
        if adult_matches and child_matches:
            adults = int(adult_matches[0])
            children = int(child_matches[0])
            preferences["num_people"] = adults + children
            preferences["hotel_preferences"]["adults"] = adults
            preferences["hotel_preferences"]["children"] = children
        
        # 提取預算
        budget_matches = re.findall(r'預算[約是]?(\d+)', content)
        if budget_matches:
            preferences["budget"] = int(budget_matches[0])
        
        # 預算級別關鍵詞
        if "便宜" in content or "經濟" in content:
            preferences["budget_level"] = "low"
        elif "高級" in content or "奢華" in content:
            preferences["budget_level"] = "high"
        elif "中等" in content:
            preferences["budget_level"] = "medium"
        
        # 提取興趣
        interest_mapping = {
            "美食": ["美食", "餐廳", "小吃", "夜市"],
            "購物": ["購物", "商場", "市場", "精品"],
            "歷史": ["歷史", "古蹟", "博物館", "文化"],
            "文化": ["文化", "藝術", "展覽", "傳統"],
            "自然": ["自然", "風景", "公園", "海灘", "山"],
            "藝術": ["藝術", "展覽", "博物館", "畫廊"],
            "休閒": ["休閒", "放鬆", "溫泉", "按摩"],
            "冒險": ["冒險", "刺激", "運動", "攀登"],
            "宗教": ["寺廟", "教堂", "宗教", "神社"]
        }
        
        for interest, keywords in interest_mapping.items():
            for keyword in keywords:
                if keyword in content and interest not in preferences["interests"]:
                    preferences["interests"].append(interest)
                    break
        
        # 儲存提取的偏好
        self.user_preferences = preferences
        
        # 如果沒有檢測到目的地，嘗試推斷
        if not preferences.get("destination"):
            for location in ["台北", "高雄", "台中", "台南", "花蓮"]:
                if location in content:
                    preferences["destination"] = f"{location}市" if location != "花蓮" else "花蓮縣"
                    break
        
        return preferences
    
    # 簡化後的同步版本
    def receive_response(self, response, is_initial=False, is_complete=False):
        """
        處理來自協調器的響應，同步版本
        """
        # 使用回調函數更新UI
        if self.update_callback:
            self.update_callback(response)
        
        return response
    
    # 傳統的異步方法，但加入同步兼容性
    async def receive_response_async(self, response, is_initial=False, is_complete=False):
        """
        處理來自協調器的響應，支持異步和同步操作
        """
        # 優先使用回調函數
        if self.update_callback:
            self.update_callback(response)
        
        return response
    
    def initiate_chat(self, user_message):
        """
        啟動與協調器代理的聊天
        """
        if not self.coordinator:
            error_message = "協調器未設置，無法處理請求。"
            self.logger.error(error_message)
            return error_message
        
        try:
            # 使用事件循環而非創建新的循環，避免多層嵌套問題
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 執行異步聊天
                result = loop.run_until_complete(self._async_initiate_chat(user_message))
                return result
            finally:
                # 確保關閉循環
                loop.close()
                
        except Exception as e:
            self.logger.error(f"啟動聊天時出錯: {str(e)}")
            return f"處理您的請求時發生錯誤: {str(e)}"
    
    async def _async_initiate_chat(self, user_message):
        """異步啟動聊天的輔助方法"""
        try:
            # 處理用戶查詢以提取偏好
            preferences = self.process_user_query(user_message)
            
            # 創建消息對象
            message = {
                "content": user_message,
                "source": self.name,
                "preferences": preferences
            }
            
            # 在嘗試與協調器通信前設置狀態
            if self.update_callback:
                self.update_callback("正在分析您的旅遊需求，請稍候...")
            
            # 使用超時機制轉發消息到協調器，避免無限等待
            try:
                response = await asyncio.wait_for(
                    self.coordinator.on_messages([message]),
                    timeout=60  # 設置一個合理的超時時間，例如60秒
                )
            except asyncio.TimeoutError:
                self.logger.warning("與協調器通信超時")
                return "處理您的請求時發生超時。請稍後再試或提供更具體的旅遊需求。"
            
            # 如果回應為空，提供備用回應
            if not response:
                response = "我正在處理您的請求，但目前無法提供完整回應。請稍後再試或提供更多細節。"
                
            return response
        except Exception as e:
            self.logger.error(f"在異步聊天過程中出錯: {str(e)}")
            return f"處理您的請求時發生錯誤: {str(e)}" 