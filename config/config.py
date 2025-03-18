"""
Configuration settings for the Traveling Assistant Multi-Agent System.
"""
import os

# System response time constraints
INITIAL_RESPONSE_TIME = 5  # seconds
COMPLETE_RESPONSE_TIME = 30  # seconds

# Mock data settings
USE_MOCK_DATA = True  # Set to False when using real APIs

# Agent configuration
AGENT_CONFIG = {
    "user_proxy": {
        "name": "User Proxy",
        "description": "Represents the user and handles user interactions.",
    },
    "hotel_agent": {
        "name": "Hotel Recommendation Agent",
        "description": "Specializes in recommending suitable accommodations based on user preferences.",
        "initial_response_timeout": 3,  # seconds
    },
    "itinerary_agent": {
        "name": "Itinerary Planning Agent",
        "description": "Specializes in planning activities and attractions around the accommodations.",
        "initial_response_timeout": 3,  # seconds
    },
    "coordinator_agent": {
        "name": "Coordinator Agent",
        "description": "Coordinates between agents and ensures timely, coherent responses.",
    },
}

# API Keys and Endpoints
API_KEY = "DhDkXZkGXaYBZhkk1Z9m9BuZDJGy"
BASE_API_URL = "https://raccoonai-agents-api.readme.io/reference"

# Communication templates
TEMPLATES = {
    "initial_response": "我們正在為您尋找最適合的旅宿選擇和行程安排，請稍候...",
    "hotel_recommendation_template": "根據您的需求，我們推薦以下旅宿：\n{hotel_recommendations}",
    "itinerary_template": "您的行程安排：\n{itinerary_plan}",
    "complete_response_template": """
# 您的旅遊計畫

## 推薦住宿
{hotel_recommendations}

## 周邊景點與活動
{attractions_recommendations}

## 交通建議
{transportation_suggestions}
"""
}

# Logging Configuration
LOGGING_CONFIG = {
    # 是否啟用 AutoGen 詳細日誌
    "enable_autogen_logging": False,
    
    # AutoGen 日誌級別 (改為警告級別，減少不必要的資訊)
    "autogen_log_level": "WARNING",
    
    # LLM 調用日誌，默認關閉以提高性能
    "log_llm_calls": False,
    
    # 如果啟用日誌，只記錄使用量以節省空間
    "log_llm_usage_only": True,
    
    # 日誌保存位置 (相對於專案根目錄)
    "log_dir": os.path.join("logs"),
    
    # 禁用 LLM 調用的文件存儲以減少IO操作
    "enable_llm_file_logging": False,
} 