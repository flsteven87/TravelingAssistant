"""
Simplified Traveling Assistant application with only UserProxyAgent.
"""
import os
import logging
import sys
import asyncio  # 引入 asyncio 模塊
from typing import List, Dict, Any, Optional
from datetime import datetime

import streamlit as st

# Add the root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 初始化日誌配置（只需在導入其他模塊前完成一次）
if 'logger_initialized' not in st.session_state:
    from utils.logger_setup import initialize_logging
    initialize_logging()
    st.session_state.logger_initialized = True

# 設定基本日誌級別
logger = logging.getLogger('traveling_assistant.app')

# 導入 autogen 的相關類
from autogen_agentchat.agents import UserProxyAgent, AssistantAgent
# 導入 OpenAI 相關配置
from autogen_ext.models.openai import OpenAIChatCompletionClient
# 導入消息類型
from autogen_agentchat.messages import TextMessage

# 獲取 API 密鑰（從環境變量或 .env 文件）
def get_openai_api_key():
    # 嘗試從環境變量獲取
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # 如果環境變量中沒有，嘗試從 .env 文件讀取
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("OPENAI_API_KEY")
        except ImportError:
            logger.warning("python-dotenv 未安裝，無法從 .env 文件讀取")
    
    return api_key

# Initialize Streamlit page config
st.set_page_config(
    page_title="旅遊規劃智能助手",
    page_icon="🏝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables."""
    # 核心聊天功能變數
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_response' not in st.session_state:
        st.session_state.current_response = ""
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'agent_initialized' not in st.session_state:
        st.session_state.agent_initialized = False
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None
    if 'travel_agent' not in st.session_state:
        st.session_state.travel_agent = None
    if 'user_proxy' not in st.session_state:
        st.session_state.user_proxy = None
    if 'last_user_input' not in st.session_state:
        st.session_state.last_user_input = ""
    if 'waiting_for_input' not in st.session_state:
        st.session_state.waiting_for_input = False
    if 'model_client' not in st.session_state:
        st.session_state.model_client = None
    
    # 日誌相關變數
    if 'log_content' not in st.session_state:
        st.session_state.log_content = ""
    
    # 新增: 用於存儲用戶輸入進行處理
    if 'user_input_queue' not in st.session_state:
        st.session_state.user_input_queue = []

def setup_ui():
    """Setup the Streamlit user interface."""
    st.title("旅遊規劃智能助手 🌎✈️")
    
    with st.expander("使用說明", expanded=False):
        st.markdown("""
        ### 使用說明
        1. 您可以使用這個助手規劃您的旅遊行程
        2. 請提供以下詳細信息以獲得最好的建議：
           - 目的地 (城市或國家)
           - 旅行日期和天數
           - 人數和特殊需求
           - 預算範圍
           - 喜好的景點類型 (如歷史古蹟、自然風光等)
        3. 助手將收集您的旅遊需求，並協助您規劃完整行程
        
        **範例問題**：「我計劃下個月帶家人去台北旅遊3天，我們有2大2小，預算中等，想看看夜市和博物館，有什麼推薦的住宿和景點嗎？」
        """)
    
    # 顯示錯誤信息
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        st.session_state.error_message = None
    
    # 檢查並處理用戶輸入佇列
    process_input_queue()
    
    # 顯示聊天界面
    display_chat()
    
    # 顯示輸入區域
    display_input_area()

def process_input_queue():
    """處理佇列中的用戶輸入"""
    # 檢查是否有等待處理的用戶輸入且當前沒有處理中的請求
    if st.session_state.user_input_queue and not st.session_state.processing:
        prompt = st.session_state.user_input_queue.pop(0)
        process_query(prompt)

def display_chat():
    """Display the chat interface with messages."""
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Display current response if processing
    if st.session_state.current_response and st.session_state.processing:
        with st.chat_message("assistant"):
            st.markdown(st.session_state.current_response)
            
            # 添加處理狀態指示器
            if st.session_state.processing:
                st.write("⏳ 正在處理中...")

def display_input_area():
    """Display the input area for user queries."""
    if prompt := st.chat_input("請告訴我您的旅遊需求...", disabled=st.session_state.processing):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat interface
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 如果在等待用戶輸入，將輸入存儲到 last_user_input
        if st.session_state.waiting_for_input:
            st.session_state.last_user_input = prompt
            st.session_state.waiting_for_input = False
        else:
            # 否則將輸入添加到佇列
            st.session_state.user_input_queue.append(prompt)
        
        # 重新運行應用以更新UI並處理輸入
        st.rerun()

# 定義用戶輸入函數供 UserProxyAgent 使用
def get_user_input(prompt: Optional[str] = None) -> str:
    """與 Streamlit 界面交互，獲取用戶輸入"""
    # 在控制台打印提示（如果有）
    if prompt:
        logger.info(f"提示用戶輸入: {prompt}")
        st.session_state.current_response = prompt
    
    # 將狀態設為等待用戶輸入
    st.session_state.waiting_for_input = True
    st.rerun()
    
    # 註意：這個函數執行到這裡會被 st.rerun() 中斷
    # 實際的輸入處理會在 display_input_area 中完成
    # 之後再次調用這個函數時，如果 last_user_input 已設置，則返回它
    
    # 這段代碼實際上不會執行，因為 rerun 後函數會重新開始
    # 但為了代碼的完整性，我們仍然包含了它
    return st.session_state.last_user_input

def setup_agents():
    """建立簡化版的代理系統，僅使用 UserProxyAgent 和 AssistantAgent"""
    try:
        # 獲取 OpenAI API Key
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("找不到 OpenAI API 密鑰，請在環境變量或 .env 文件中設置 OPENAI_API_KEY")
        
        # 創建 OpenAI 客戶端 (如果不存在)
        if st.session_state.model_client is None:
            st.session_state.model_client = OpenAIChatCompletionClient(
                api_key=api_key,
                model="gpt-3.5-turbo"  # 使用更便宜的 gpt-3.5-turbo 模型
            )
        model_client = st.session_state.model_client
        
        # 創建旅遊助手代理
        travel_agent = AssistantAgent(
            name="travel_agent",
            system_message="""
            你是一個專業的旅遊規劃助手。你的任務是幫助用戶規劃完整的旅遊行程。
            
            請確保收集以下關鍵資訊:
            1. 目的地 (必須)
            2. 旅行日期和天數 (必須)
            3. 旅行人數和組成 (成人、兒童數量)
            4. 預算範圍
            5. 偏好的景點類型和活動
            6. 飲食偏好或限制
            7. 住宿偏好
            8. 交通偏好
            
            如果用戶未提供足夠資訊，請有禮貌地詢問缺少的資訊。
            當你收集完所有必要資訊後，請生成一個包含 "FINAL PLAN" 字樣的最終旅遊計劃回應。
            """,
            model_client=model_client  # 提供必要的 model_client 參數
        )
        logger.info("Travel agent is created.")
        
        # 創建使用者代理 - 使用 autogen 0.4.x 版本支持的參數
        user_proxy = UserProxyAgent(
            name="user_proxy",
            description="代表用戶與旅遊規劃助手對話的代理",
            input_func=get_user_input  # 使用自定義的輸入函數
        )
        logger.info("User proxy is created.")
        
        # 保存到 session_state
        st.session_state.travel_agent = travel_agent
        st.session_state.user_proxy = user_proxy
        st.session_state.agent_initialized = True
        
        return {
            "travel_agent": travel_agent,
            "user_proxy": user_proxy
        }
    except Exception as e:
        logger.error(f"設置代理系統錯誤: {str(e)}")
        raise

def update_current_response(response):
    """更新當前響應以顯示在界面上"""
    st.session_state.current_response = response
    st.rerun()

def process_query(prompt):
    """處理用戶查詢"""
    if st.session_state.processing:
        # 已經有處理中的請求，不處理
        logger.info("已有處理中的請求，忽略新請求")
        return
    
    st.session_state.processing = True
    st.session_state.current_response = "正在分析您的旅遊需求..."
    
    try:
        # 初始化代理系統（如果需要）
        if not st.session_state.agent_initialized:
            with st.spinner("正在初始化旅遊助手系統..."):
                logger.info("初始化代理系統...")
                setup_agents()
                logger.info("代理系統初始化成功")
        
        # 取得代理
        travel_agent = st.session_state.travel_agent
        
        # 將對話保存在 session_state
        st.session_state.last_user_input = prompt
        
        # 創建事件循環來運行非同步函數
        logger.info("創建事件循環...")
        try:
            # 使用直接的 API 調用，避免代理複雜度
            message = TextMessage(content=prompt, source="user", type="TextMessage")
            logger.info(f"使用消息: {message}")
            
            # 創建新的事件循環
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 調用 travel_agent.run
            logger.info("調用 travel_agent.run...")
            response = loop.run_until_complete(travel_agent.run(task=message))
            logger.info(f"取得回應: {response}")
            loop.close()
            
            # 從 response 中提取文本
            final_response = ""
            if hasattr(response, "messages") and response.messages:
                for msg in response.messages:
                    if hasattr(msg, "source") and msg.source == "travel_agent":
                        final_response = msg.content
                        break
            
            # 如果無法從消息中提取，使用字符串表示
            if not final_response:
                final_response = str(response)
                
            logger.info(f"最終回應: {final_response[:50]}...")
            st.session_state.messages.append({"role": "assistant", "content": final_response})
            
        except Exception as e:
            logger.error(f"非同步處理過程中出錯: {str(e)}")
            # 如果沒有獲得回應，提供默認回應
            default_response = "抱歉，處理您的請求時出現問題。請再試一次，或提供更多旅遊細節。"
            st.session_state.messages.append({"role": "assistant", "content": default_response})
            
    except Exception as e:
        # 處理錯誤
        logger.error(f"處理查詢時出錯: {str(e)}")
        error_message = f"處理請求時發生錯誤: {str(e)}"
        st.session_state.error_message = error_message
    
    finally:
        # 完成處理，重置狀態
        st.session_state.processing = False
        st.session_state.current_response = ""
        # 安全檢查，確保我們可以調用 rerun
        st.rerun()

def add_sidebar():
    """Add sidebar with application controls."""
    with st.sidebar:
        st.header("控制面板")
        
        # Add clear chat history button
        if st.button("清除對話歷史", type="primary"):
            # Ensure no background processing is happening
            if st.session_state.processing:
                st.warning("請等待當前請求處理完成後再清除對話歷史...")
                return
            
            st.session_state.messages = []
            st.session_state.current_response = ""
            st.session_state.processing = False
            st.session_state.user_input_queue = []
            st.session_state.last_user_input = ""
            st.session_state.waiting_for_input = False
            
            # Reset agent initialization flag to reinitialize the agent system
            st.session_state.agent_initialized = False
            st.session_state.travel_agent = None
            st.session_state.user_proxy = None
            
            st.success("對話歷史已清除！")
            
            # Rerun to update UI
            st.rerun()
        
        st.divider()
        
        # 簡化的日誌檢視功能
        with st.expander("查看系統日誌", expanded=False):
            if st.button("刷新日誌"):
                refresh_logs()
            
            if st.session_state.log_content:
                with st.container(height=400):
                    st.text_area("最近的系統日誌", value=st.session_state.log_content, height=380, disabled=True)
        
        st.divider()
        

def refresh_logs():
    """刷新並顯示最新的系統日誌."""
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        
        # 創建日誌目錄（如果不存在）
        os.makedirs(log_dir, exist_ok=True)
        
        # 尋找最新的應用程序日誌文件
        app_logs = [f for f in os.listdir(log_dir) if f.startswith("app_") and f.endswith(".log")]
        if app_logs:
            latest_log = sorted(app_logs)[-1]
            log_path = os.path.join(log_dir, latest_log)
            
            # 讀取最新的日誌條目（最後100行）
            with open(log_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-100:] if len(all_lines) > 100 else all_lines
                st.session_state.log_content = "".join(last_lines)
        else:
            st.session_state.log_content = "尚無日誌文件可顯示"
    except Exception as e:
        logger.error(f"刷新日誌時出錯: {str(e)}")
        st.session_state.log_content = f"載入日誌時出錯: {str(e)}"

def main():
    """Main application entry point."""
    try:
        # Initialize session state
        initialize_session_state()
        
        # 確保日誌目錄存在
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # 強制刷新日誌
        log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        logger.info("應用程序啟動")
        
        # Setup sidebar
        add_sidebar()
        
        # Setup main UI
        setup_ui()
        
    except Exception as e:
        logger.error(f"應用程序主要錯誤: {str(e)}")
        st.error(f"應用程序錯誤: {str(e)}")

if __name__ == "__main__":
    main() 