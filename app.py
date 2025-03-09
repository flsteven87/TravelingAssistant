import streamlit as st
import time
import os
from dotenv import load_dotenv
import sys

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 載入環境變數
load_dotenv()

# 導入 OrchestratorAgent
from src.agents.orchestrator_agent import OrchestratorAgent

# 頁面配置
st.set_page_config(
    page_title="旅遊助手",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if "agent" not in st.session_state:
    st.session_state.agent = OrchestratorAgent(verbose=True)

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

# 標題
st.title("✈️ 旅遊助手")
st.subheader("您的個人旅遊規劃專家")

# 側邊欄
with st.sidebar:
    st.header("關於")
    st.write("""
    這是一個旅遊助手應用程序，可以幫助您規劃旅行、推薦住宿和安排行程。
    
    使用方法：
    1. 在輸入框中輸入您的旅遊需求
    2. 助手會在5秒內給出初步回應
    3. 在30秒內提供完整的旅遊建議
    
    示例問題：
    - 我想去台北旅遊，有什麼好的住宿推薦？
    - 請幫我規劃一個三天兩夜的花蓮行程
    - 我和家人想去墾丁，預算5000元，有適合的住宿嗎？
    """)
    
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
        # 模擬處理時間和進度更新
        with st.spinner("正在生成完整回應..."):
            # 更新進度
            for i in range(3, 10, 1):
                time.sleep(0.5)  # 模擬處理時間
                st.session_state.progress = i / 10
                st.rerun()
            
            # 獲取完整回應
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