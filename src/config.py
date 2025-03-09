"""
系統配置文件
"""
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# API 設定
API_BASE_URL = "https://k6oayrgulgb5sasvwj3tsy7l7u0tikfd.lambda-url.ap-northeast-1.on.aws"  # 修正為正確的 Lambda URL
API_KEY = os.getenv("API_KEY", "DhDkXZkGXaYBZhkk1Z9m9BuZDJGy")  # 使用預設的外部專用 API Key

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API Headers
API_HEADERS = {
    "accept": "application/json",
    "Authorization": API_KEY
}

# 旅宿 API 路徑
HOTEL_API = {
    "counties": "/api/v3/tools/interview_test/taiwan_hotels/counties",
    "districts": "/api/v3/tools/interview_test/taiwan_hotels/districts",
    "hotel_types": "/api/v3/tools/interview_test/taiwan_hotels/hotel_group/types",
    "hotel_facilities": "/api/v3/tools/interview_test/taiwan_hotels/hotel/facilities",
    "room_facilities": "/api/v3/tools/interview_test/taiwan_hotels/hotel/room_type/facilities",
    "bed_types": "/api/v3/tools/interview_test/taiwan_hotels/hotel/room_type/bed_types",
    "hotels": "/api/v3/tools/interview_test/taiwan_hotels/hotels",
    "hotel_fuzzy_match": "/api/v3/tools/interview_test/taiwan_hotels/hotel/fuzzy_match",
    "hotel_detail": "/api/v3/tools/interview_test/taiwan_hotels/hotel/detail",
    "hotel_supply": "/api/v3/tools/interview_test/taiwan_hotels/hotel/supply",
    "plans": "/api/v3/tools/interview_test/taiwan_hotels/plans",
    "vacancies": "/api/v3/tools/interview_test/taiwan_hotels/hotel/vacancies",
}

# 地點 API 路徑
PLACE_API = {
    "nearby_search": "/api/v3/tools/external/gcp/places/nearby_search_with_query",
}

# 系統設定
SYSTEM_CONFIG = {
    "quick_response_timeout": 5,  # 快速回應超時時間（秒）
    "complete_response_timeout": 30,  # 完整回應超時時間（秒）
    "max_retries": 3,  # API 請求最大重試次數
    "retry_delay": 1,  # 重試延遲時間（秒）
}

# 日誌設定
LOG_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),  # 日誌級別，可以是 DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "%(asctime)s [%(name)s] %(levelname)s: %(message)s",  # 日誌格式
    "date_format": "%Y-%m-%d %H:%M:%S",  # 日期格式
    "colored_output": True,  # 是否啟用彩色輸出
    "show_full_path": False,  # 是否顯示完整路徑
    "truncate_long_messages": True,  # 是否截斷長訊息
    "max_message_length": 500,  # 最大訊息長度
    "show_params_once": True,  # 是否只顯示參數一次
    "log_to_file": os.getenv("LOG_TO_FILE", "false").lower() == "true",  # 是否記錄到檔案
    "log_file_path": os.getenv("LOG_FILE_PATH", "logs/app.log"),  # 日誌檔案路徑
    "log_file_level": os.getenv("LOG_FILE_LEVEL", "INFO"),  # 日誌檔案級別
    
    # 模組顏色映射
    "module_colors": {
        "OrchestratorAgent": "BRIGHT_CYAN",
        "HotelAgent": "BRIGHT_GREEN",
        "ItineraryAgent": "BRIGHT_MAGENTA",
        "API": "BRIGHT_YELLOW",
        "DEFAULT": "BRIGHT_WHITE"
    }
}

# 初始化日誌系統
def init_logging():
    """初始化日誌系統"""
    from .utils import logging_utils
    
    # 配置日誌系統
    logging_utils.configure({
        "colored_output": LOG_CONFIG["colored_output"],
        "show_full_path": LOG_CONFIG["show_full_path"],
        "truncate_long_messages": LOG_CONFIG["truncate_long_messages"],
        "max_message_length": LOG_CONFIG["max_message_length"],
        "show_params_once": LOG_CONFIG["show_params_once"],
        "log_to_file": LOG_CONFIG["log_to_file"],
        "log_file_path": LOG_CONFIG["log_file_path"],
        "log_file_level": LOG_CONFIG["log_file_level"].lower()
    })
    
    # 設置模組顏色
    for module, color in LOG_CONFIG["module_colors"].items():
        if hasattr(logging_utils.Colors, color):
            logging_utils.MODULE_COLORS[module] = getattr(logging_utils.Colors, color)
    
    # 創建根日誌記錄器
    root_logger = logging_utils.setup_logger(
        name="root",
        level=LOG_CONFIG["level"].lower(),
        format_str=LOG_CONFIG["format"],
        date_format=LOG_CONFIG["date_format"]
    )
    
    return root_logger
