import streamlit as st
import time
import os
from dotenv import load_dotenv
import sys
import asyncio
import datetime
import atexit

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 載入環境變數
load_dotenv()

# 初始化日誌系統
from src.config import init_logging
logger = init_logging()

# 導入 OrchestratorAgent、HotelAgent 和 ItineraryAgent
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.hotel_agent import HotelAgent
from src.agents.itinerary_agent import ItineraryAgent
from src.api.hotel_api import HotelAPI
from src.utils import logging_utils

# 記錄應用程式啟動
logging_utils.info(logger, "旅遊助手應用程式啟動")

# 頁面配置
st.set_page_config(
    page_title="旅遊助手",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if "agent" not in st.session_state:
    logging_utils.info(logger, "初始化 Agent")
    
    # 創建 OrchestratorAgent
    orchestrator = OrchestratorAgent(verbose=True)
    
    # 創建 HotelAgent
    hotel_agent = HotelAgent(verbose=True)
    
    # 創建 ItineraryAgent
    itinerary_agent = ItineraryAgent(verbose=True)
    
    # 將 HotelAgent 和 ItineraryAgent 添加為 OrchestratorAgent 的協作者
    orchestrator.add_collaborator(hotel_agent)
    orchestrator.add_collaborator(itinerary_agent)
    
    # 保存到 session state
    st.session_state.agent = orchestrator
    
    # 註冊 Streamlit 會話結束時的清理函數
    def cleanup_resources():
        logging_utils.info(logger, "正在清理資源...")
        # 關閉 API 客戶端
        if hasattr(hotel_agent, 'hotel_api') and hotel_agent.hotel_api and hasattr(hotel_agent.hotel_api, 'client'):
            asyncio.run(hotel_agent.hotel_api.client.close())
        if hasattr(itinerary_agent, 'place_api') and itinerary_agent.place_api and hasattr(itinerary_agent.place_api, 'client'):
            asyncio.run(itinerary_agent.place_api.client.close())
        logging_utils.info(logger, "資源清理完成")
    
    # 註冊清理函數
    atexit.register(cleanup_resources)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "processing" not in st.session_state:
    st.session_state.processing = False

if "progress" not in st.session_state:
    st.session_state.progress = 0.0

if "quick_response" not in st.session_state:
    st.session_state.quick_response = None

if "complete_response" not in st.session_state:
    st.session_state.complete_response = None

if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

if "form_data" not in st.session_state:
    st.session_state.form_data = {}

if "counties" not in st.session_state:
    st.session_state.counties = []

if "hotel_types" not in st.session_state:
    st.session_state.hotel_types = []

# 標題
st.title("✈️ 旅遊助手")
st.subheader("您的個人旅遊規劃專家")

# 異步加載縣市和飯店類型數據
async def load_form_data():
    logging_utils.info(logger, "開始加載表單數據", "load_form_data")
    
    hotel_api = HotelAPI()
    
    try:
        # 獲取縣市列表
        counties_task = hotel_api.get_counties()
        
        # 獲取飯店類型列表
        hotel_types_task = hotel_api.get_hotel_types()
        
        # 等待所有任務完成
        counties, hotel_types = await asyncio.gather(counties_task, hotel_types_task)
        
        logging_utils.info(logger, "表單數據加載完成", "load_form_data", 
                          {"counties_count": len(counties), "hotel_types_count": len(hotel_types)})
        
        return counties, hotel_types
    finally:
        # 確保 API 客戶端被關閉
        if hotel_api and hotel_api.client:
            await hotel_api.client.close()
            logging_utils.info(logger, "表單數據加載 API 客戶端已關閉", "load_form_data")

# 使用 Streamlit 的 spinner 顯示加載狀態
@st.cache_data(ttl=3600)  # 緩存數據1小時
def get_form_data():
    with st.spinner("正在加載數據..."):
        # 使用 asyncio 運行異步函數
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            counties, hotel_types = loop.run_until_complete(load_form_data())
            return counties, hotel_types
        finally:
            # 確保事件循環被關閉
            loop.close()

# 側邊欄
with st.sidebar:
    st.header("旅遊資訊表單")
    
    # 如果縣市和飯店類型數據尚未加載，則加載它們
    if not st.session_state.counties or not st.session_state.hotel_types:
        logging_utils.info(logger, "加載縣市和飯店類型數據", "sidebar")
        counties, hotel_types = get_form_data()
        st.session_state.counties = counties
        st.session_state.hotel_types = hotel_types
    
    # 如果表單已提交，顯示表單數據
    if st.session_state.form_submitted:
        st.write("### 您的旅遊資訊")
        
        form_data = st.session_state.form_data
        
        st.write(f"**目的地:** {form_data['county_name']}")
        st.write(f"**入住日期:** {form_data['check_in_date']}")
        st.write(f"**退房日期:** {form_data['check_out_date']}")
        st.write(f"**人數:** {form_data['adults']} 成人, {form_data['children']} 兒童")
        
        if form_data['hotel_type_names']:
            st.write(f"**喜好的飯店類型:** {', '.join(form_data['hotel_type_names'])}")
        else:
            st.write("**喜好的飯店類型:** 無特別偏好")
        
        st.write(f"**預算範圍:** NT${form_data['budget_min']} - NT${form_data['budget_max']} / 晚")
        
        # 返回按鈕
        col1, col2 = st.columns(2)
        with col1:
            if st.button("修改資訊"):
                logging_utils.info(logger, "用戶點擊修改資訊按鈕", "sidebar")
                st.session_state.form_submitted = False
                st.rerun()
        
        # 開始規劃按鈕
        with col2:
            if st.button("開始規劃旅程"):
                logging_utils.info(logger, "用戶點擊開始規劃旅程按鈕", "sidebar")
                
                # 將表單數據轉換為自然語言查詢
                query = f"我想去{form_data['county_name']}旅遊，入住日期是{form_data['check_in_date']}，退房日期是{form_data['check_out_date']}，"
                query += f"有{form_data['adults']}位成人"
                
                if form_data['children'] > 0:
                    query += f"和{form_data['children']}位兒童"
                
                if form_data['hotel_type_names']:
                    query += f"，我喜歡的飯店類型是{', '.join(form_data['hotel_type_names'])}"
                
                query += f"，預算範圍是每晚{form_data['budget_min']}到{form_data['budget_max']}元。請幫我推薦適合的住宿和規劃行程。"
                
                logging_utils.info(logger, "生成查詢", "sidebar", {"query": query[:100] + "..."})
                
                # 添加用戶消息到聊天歷史
                st.session_state.messages.append({"role": "user", "content": query})
                
                # 設置處理狀態
                st.session_state.processing = True
                
                # 重新運行腳本以更新界面
                st.rerun()
    else:
        # 創建表單
        with st.form("travel_info_form"):
            # 目標旅遊縣市（下拉式選單）
            county_options = [{"label": county.get("name", ""), "value": county.get("id", "")} 
                             for county in st.session_state.counties]
            county_id = st.selectbox(
                "目標旅遊縣市",
                options=[option["value"] for option in county_options],
                format_func=lambda x: next((option["label"] for option in county_options if option["value"] == x), ""),
                help="請選擇您想要旅遊的縣市"
            )
            
            # 起迄日期（日期選擇器）
            col1, col2 = st.columns(2)
            with col1:
                today = datetime.date.today()
                check_in_date = st.date_input(
                    "入住日期",
                    value=today + datetime.timedelta(days=1),
                    min_value=today,
                    help="請選擇您的入住日期"
                )
            with col2:
                check_out_date = st.date_input(
                    "退房日期",
                    value=today + datetime.timedelta(days=3),
                    min_value=check_in_date,
                    help="請選擇您的退房日期"
                )
            
            # 人數（數字輸入）
            col1, col2 = st.columns(2)
            with col1:
                adults = st.number_input(
                    "成人數量",
                    min_value=1,
                    max_value=10,
                    value=2,
                    step=1,
                    help="請輸入成人數量（12歲以上）"
                )
            with col2:
                children = st.number_input(
                    "兒童數量",
                    min_value=0,
                    max_value=10,
                    value=0,
                    step=1,
                    help="請輸入兒童數量（12歲以下）"
                )
            
            # 飯店類型（多選框）
            hotel_type_options = [{"label": hotel_type.get("name", ""), "value": hotel_type.get("type", "")} 
                                 for hotel_type in st.session_state.hotel_types]
            hotel_types_selected = st.multiselect(
                "喜歡的飯店類型",
                options=[option["value"] for option in hotel_type_options],
                format_func=lambda x: next((option["label"] for option in hotel_type_options if option["value"] == x), ""),
                help="請選擇您喜歡的飯店類型（可多選）"
            )
            
            # 預算範圍（滑桿）
            budget = st.slider(
                "每晚預算範圍（新台幣）",
                min_value=1000,
                max_value=10000,
                value=(2000, 5000),
                step=500,
                help="請選擇您的每晚預算範圍"
            )
            
            # 提交按鈕
            submitted = st.form_submit_button("提交")
            
            if submitted:
                logging_utils.info(logger, "用戶提交表單", "form")
                
                # 收集表單數據
                form_data = {
                    "county_id": county_id,
                    "county_name": next((county["name"] for county in st.session_state.counties if county["id"] == county_id), ""),
                    "check_in_date": check_in_date.strftime("%Y-%m-%d"),
                    "check_out_date": check_out_date.strftime("%Y-%m-%d"),
                    "adults": adults,
                    "children": children,
                    "hotel_types": hotel_types_selected,
                    "hotel_type_names": [next((hotel_type["name"] for hotel_type in st.session_state.hotel_types if hotel_type["type"] == type_id), "") 
                                       for type_id in hotel_types_selected],
                    "budget_min": budget[0],
                    "budget_max": budget[1]
                }
                
                # 保存表單數據到 session state
                st.session_state.form_data = form_data
                st.session_state.form_submitted = True
                
                logging_utils.info(logger, "表單數據已保存", "form", 
                                  {"county": form_data["county_name"], "dates": f"{form_data['check_in_date']} to {form_data['check_out_date']}"})
                
                # 重新運行腳本以更新界面
                st.rerun()

# 聊天界面
st.divider()

# 顯示聊天歷史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 如果正在處理請求
if st.session_state.processing:
    # 顯示助手的回應
    with st.chat_message("assistant"):
        # 如果快速回應尚未生成
        if st.session_state.quick_response is None:
            # 創建空白容器
            response_container = st.empty()
            
            # 創建進度條
            progress_bar = st.progress(0)
            
            # 獲取 Agent
            agent = st.session_state.agent
            
            # 獲取最後一條用戶消息
            user_message = st.session_state.messages[-1]["content"]
            
            # 記錄開始處理時間
            start_time = time.time()
            
            logging_utils.info(logger, "開始處理用戶查詢", "chat", {"query": user_message[:100] + "..."})
            
            # 調用 Agent 處理用戶消息
            try:
                result = agent.chat(user_message)
                
                # 獲取快速回應
                quick_response = result.get("quick_response", "正在處理您的請求，請稍候...")
                
                # 更新快速回應
                st.session_state.quick_response = quick_response
                
                # 顯示快速回應
                response_container.markdown(quick_response)
                
                # 更新進度條
                progress_bar.progress(0.3)
                
                # 獲取完整回應
                complete_response = result.get("complete_response", "")
                
                # 更新完整回應
                st.session_state.complete_response = complete_response
                
                # 顯示完整回應
                response_container.markdown(complete_response)
                
                # 記錄結束處理時間
                end_time = time.time()
                execution_time = end_time - start_time
                
                logging_utils.info(logger, "用戶查詢處理完成", "chat", 
                                  {"execution_time": f"{execution_time:.2f}秒", "response_length": len(complete_response)})
                
                # 添加助手消息到聊天歷史
                st.session_state.messages.append({"role": "assistant", "content": complete_response})
            except Exception as e:
                logging_utils.error(logger, f"處理用戶查詢時發生錯誤: {str(e)}", "chat")
                # 添加錯誤消息到聊天歷史
                error_message = "抱歉，處理您的請求時發生了錯誤。請稍後再試。"
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                response_container.markdown(error_message)
            finally:
                # 重置處理狀態
                st.session_state.processing = False
                st.session_state.quick_response = None
                st.session_state.complete_response = None
                
                # 重新運行腳本以更新界面
                st.rerun()
        else:
            # 如果完整回應已生成
            if st.session_state.complete_response:
                st.markdown(st.session_state.complete_response)
            else:
                st.markdown(st.session_state.quick_response)

# 用戶輸入
if not st.session_state.processing:
    if user_input := st.chat_input("請輸入您的問題..."):
        # 添加用戶消息到聊天歷史
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        logging_utils.info(logger, "收到用戶輸入", "chat_input", {"input": user_input[:100] + "..." if len(user_input) > 100 else user_input})
        
        # 設置處理狀態
        st.session_state.processing = True
        
        # 重新運行腳本以更新界面
        st.rerun()

# 重置按鈕
with st.sidebar:
    st.divider()
    if st.button("重置對話"):
        logging_utils.info(logger, "用戶重置對話", "reset")
        
        # 清除對話歷史
        st.session_state.agent.clear_conversation()
        st.session_state.messages = []
        
        # 重置處理狀態
        st.session_state.processing = False
        st.session_state.quick_response = None
        st.session_state.complete_response = None
        
        # 重新運行腳本以更新界面
        st.rerun()

# 頁腳
st.divider()
st.caption("© 2025 旅遊助手 | 由 Multi-Agent 系統提供支持") 
