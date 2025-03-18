"""
日誌設置和配置文件
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path to allow module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

class ImmediateFileHandler(logging.FileHandler):
    """立即寫入文件的處理器，不等待緩衝"""
    
    def emit(self, record):
        """覆蓋標準的 emit 方法，確保每條記錄都被立即寫入"""
        super().emit(record)
        self.flush()  # 立即寫入文件

def setup_app_logging():
    """
    設置應用程序的基本日誌配置
    """
    try:
        # 創建日誌目錄
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            config.LOGGING_CONFIG["log_dir"]
        )
        os.makedirs(log_dir, exist_ok=True)
        
        # 設置日誌文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"app_{timestamp}.log")
        
        # 設置格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 獲取根日誌記錄器並配置
        root_logger = logging.getLogger("traveling_assistant")
        
        # 重要：清除所有現有處理器，避免重複日誌
        if root_logger.handlers:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
        
        root_logger.setLevel(logging.WARNING)  # 提高日誌級別，減少記錄
        
        # 使用文件處理器
        file_handler = ImmediateFileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 控制台處理器，只處理錯誤及以上
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.ERROR)  # 只顯示錯誤及以上級別
        root_logger.addHandler(console_handler)
        
        # 防止日誌傳播到父處理器
        root_logger.propagate = False
        
        root_logger.info(f"應用程序日誌已設置。日誌文件: {log_file}")
        
        return True
    except Exception as e:
        print(f"設置應用程序日誌時出錯: {str(e)}")
        return False

def setup_autogen_logging():
    """
    簡化的 AutoGen 日誌配置，只有在啟用時才設置
    """
    # 如果禁用 AutoGen 日誌，直接返回
    if not config.LOGGING_CONFIG.get("enable_autogen_logging", False):
        return True
    
    try:
        # 嘗試導入 AutoGen 日誌
        autogen_logging = None
        try:
            from autogen_agentchat import logging as autogen_logging
            # 自定義 logger 名稱
            TRACE_LOGGER_NAME = "autogen_agentchat.trace"
            EVENT_LOGGER_NAME = "autogen_agentchat.event"
        except ImportError:
            print("無法導入 AutoGen 日誌模組，日誌功能將受限")
            return False
        
        log_config = config.LOGGING_CONFIG
        log_level = getattr(logging, log_config["autogen_log_level"])
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), log_config["log_dir"])
        
        # 為 AutoGen 設置基本日誌 (簡化版)
        for logger_name in [TRACE_LOGGER_NAME, EVENT_LOGGER_NAME]:
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)
        
        return True
    except Exception as e:
        print(f"設置 AutoGen 日誌時出錯: {str(e)}")
        return False

def initialize_logging():
    """
    初始化所有日誌設置
    """
    # 先設置應用程序日誌
    app_log_success = setup_app_logging()
    
    # 再設置 AutoGen 日誌
    autogen_log_success = setup_autogen_logging()
    
    return app_log_success 