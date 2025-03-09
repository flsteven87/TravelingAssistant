import streamlit as st
import time
import os
from dotenv import load_dotenv
import sys
import asyncio
import datetime

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 載入環境變數
load_dotenv()

# 導入 OrchestratorAgent 和 HotelAPI
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.hotel_agent import HotelAgent
from src.api.hotel_api import HotelAPI

# 頁面配置
st.set_page_config(
    page_title="旅遊助手",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if "agent" not in st.session_state:
    # 創建 OrchestratorAgent
    orchestrator = OrchestratorAgent(verbose=True)
    
    # 創建 HotelAgent
    hotel_agent = HotelAgent(verbose=True)
    
    # 將 HotelAgent 添加為 OrchestratorAgent 的協作者
    orchestrator.add_collaborator(hotel_agent)
    
    # 保存到 session state
    st.session_state.agent = orchestrator

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
    hotel_api = HotelAPI()
    
    # 獲取縣市列表
    counties_task = hotel_api.get_counties()
    
    # 獲取飯店類型列表
    hotel_types_task = hotel_api.get_hotel_types()
    
    # 等待所有任務完成
    counties, hotel_types = await asyncio.gather(counties_task, hotel_types_task)
    
    # 關閉 API 客戶端
    await hotel_api.client.close()
    
    return counties, hotel_types

# 使用 Streamlit 的 spinner 顯示加載狀態
@st.cache_data(ttl=3600)  # 緩存數據1小時
def get_form_data():
    with st.spinner("正在加載數據..."):
        # 使用 asyncio 運行異步函數
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        counties, hotel_types = loop.run_until_complete(load_form_data())
        loop.close()
        return counties, hotel_types

# 側邊欄
with st.sidebar:
    st.header("旅遊資訊表單")
    
    # 如果縣市和飯店類型數據尚未加載，則加載它們
    if not st.session_state.counties or not st.session_state.hotel_types:
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
                st.session_state.form_submitted = False
                st.rerun()
        
        # 開始規劃按鈕
        with col2:
            if st.button("開始規劃旅程"):
                # 將表單數據轉換為自然語言查詢
                query = f"我想去{form_data['county_name']}旅遊，入住日期是{form_data['check_in_date']}，退房日期是{form_data['check_out_date']}，"
                query += f"有{form_data['adults']}位成人"
                
                if form_data['children'] > 0:
                    query += f"和{form_data['children']}位兒童"
                
                if form_data['hotel_type_names']:
                    query += f"，我喜歡的飯店類型是{', '.join(form_data['hotel_type_names'])}"
                
                query += f"，預算範圍是每晚{form_data['budget_min']}到{form_data['budget_max']}元。請幫我推薦適合的住宿和規劃行程。"
                
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
                
                # 顯示成功消息
                st.success("表單已提交！正在處理您的請求...")
                
                # 重定向到主頁面
                st.rerun()
    
    st.divider()
    
    st.header("設置")
    verbose = st.checkbox("顯示詳細日誌", value=True)
    if verbose != st.session_state.agent.verbose:
        st.session_state.agent.verbose = verbose
    
    if st.button("清除對話歷史"):
        st.session_state.agent.clear_conversation()
        st.session_state.messages = []
        st.session_state.quick_response = None
        st.session_state.complete_response = None
        st.session_state.progress = 0.0
        st.success("對話歷史已清除")
    
    st.header("關於")
    st.write("""
    這是一個旅遊助手應用程序，可以幫助您規劃旅行、推薦住宿和安排行程。
    
    使用方法：
    1. 在側邊欄填寫旅遊資訊表單
    2. 或直接在聊天框中輸入您的旅遊需求
    3. 助手會在5秒內給出初步回應
    4. 在30秒內提供完整的旅遊建議
    
    示例問題：
    - 我想去台北旅遊，有什麼好的住宿推薦？
    - 請幫我規劃一個三天兩夜的花蓮行程
    - 我和家人想去墾丁，預算5000元，有適合的住宿嗎？
    """)

# 聊天容器
chat_container = st.container()

# 顯示聊天歷史
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])

# 進度條
if st.session_state.processing:
    st.progress(st.session_state.progress)

# 輸入框
user_input = st.chat_input("輸入您的旅遊需求", disabled=st.session_state.processing)

# 處理用戶輸入
if user_input and not st.session_state.processing:
    # 設置處理狀態
    st.session_state.processing = True
    st.session_state.progress = 0.0
    st.session_state.quick_response = None
    st.session_state.complete_response = None
    
    # 添加用戶消息到聊天歷史
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 重新運行腳本以更新界面
    st.rerun()

# 處理 Agent 回應
if st.session_state.processing:
    # 如果還沒有快速回應，生成快速回應
    if not st.session_state.quick_response:
        latest_user_message = st.session_state.messages[-1]["content"]
        
        # 使用 Agent 生成快速回應
        with st.spinner("正在生成初步回應..."):
            start_time = time.time()
            result = st.session_state.agent.chat(latest_user_message)
            st.session_state.quick_response = result["quick_response"]
            st.session_state.progress = 0.3
        
        # 添加快速回應到聊天歷史
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.quick_response})
        
        # 重新運行腳本以更新界面
        st.rerun()
    
    # 如果有快速回應但沒有完整回應，生成完整回應
    elif not st.session_state.complete_response:
        # 使用 spinner 顯示處理狀態
        with st.spinner("正在生成完整回應..."):
            # 直接獲取完整回應，不再使用模擬進度的循環
            st.session_state.complete_response = st.session_state.agent.task_result["complete_response"]
            st.session_state.progress = 1.0
        
        # 更新最後一條助手消息為完整回應
        st.session_state.messages[-1]["content"] = st.session_state.complete_response
        
        # 重置處理狀態
        st.session_state.processing = False
        
        # 重新運行腳本以更新界面
        st.rerun()

# 頁腳
st.divider()
st.caption("© 2025 旅遊助手 | 由 Multi-Agent 系統提供支持") 
