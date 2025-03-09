"""
系統配置文件
"""
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# API 設定
API_BASE_URL = "https://k6oayrgulgb5sasvwj3tsy7l7u0tikfd.lambda-url.ap-northeast-1.on.aws"  # 修正為正確的 Lambda URL
API_KEY = os.getenv("API_KEY")  # 使用預設的外部專用 API Key

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
    "level": "INFO",  # 使用 INFO 級別，減少不必要的 DEBUG 日誌
    "format": "{time} | {level} | {message}",
    "file": "logs/app.log",
}
