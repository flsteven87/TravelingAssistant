"""
日誌工具模組，提供統一的日誌設定和記錄功能
"""
import logging
import os
import json
import traceback
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import sys

# 顏色代碼
class Colors:
    """ANSI 顏色代碼"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # 背景色
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # 亮色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

# 日誌級別映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# 日誌級別顏色映射
LEVEL_COLORS = {
    logging.DEBUG: Colors.BRIGHT_BLACK,
    logging.INFO: Colors.BRIGHT_BLUE,
    logging.WARNING: Colors.BRIGHT_YELLOW,
    logging.ERROR: Colors.BRIGHT_RED,
    logging.CRITICAL: Colors.BG_RED + Colors.WHITE
}

# 模組顏色映射
MODULE_COLORS = {
    "OrchestratorAgent": Colors.BRIGHT_CYAN,
    "HotelAgent": Colors.BRIGHT_GREEN,
    "ItineraryAgent": Colors.BRIGHT_MAGENTA,
    "API": Colors.BRIGHT_YELLOW,
    "DEFAULT": Colors.BRIGHT_WHITE
}

# 默認日誌格式
DEFAULT_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 日誌記錄器快取，避免重複創建
_loggers: Dict[str, logging.Logger] = {}

# 全局設定
_config = {
    "colored_output": True,
    "show_full_path": False,
    "truncate_long_messages": True,
    "max_message_length": 500,
    "show_params_once": True,
    "params_shown": set(),
    "log_to_file": False,
    "log_file_path": "logs/app.log",
    "log_file_level": "info"
}

def configure(config: Dict[str, Any]) -> None:
    """
    配置日誌系統
    
    Args:
        config: 配置字典，可包含以下鍵：
            - colored_output: 是否啟用彩色輸出
            - show_full_path: 是否顯示完整路徑
            - truncate_long_messages: 是否截斷長訊息
            - max_message_length: 最大訊息長度
            - show_params_once: 是否只顯示參數一次
            - log_to_file: 是否記錄到檔案
            - log_file_path: 日誌檔案路徑
            - log_file_level: 日誌檔案級別
    """
    global _config
    _config.update(config)
    
    # 如果啟用了檔案日誌，確保目錄存在
    if _config["log_to_file"]:
        os.makedirs(os.path.dirname(_config["log_file_path"]), exist_ok=True)

class ColoredFormatter(logging.Formatter):
    """自定義彩色格式化器"""
    
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
    
    def format(self, record):
        # 獲取原始格式化訊息
        message = super().format(record)
        
        # 如果禁用彩色輸出，直接返回
        if not _config["colored_output"]:
            return message
        
        # 獲取級別顏色
        level_color = LEVEL_COLORS.get(record.levelno, Colors.RESET)
        
        # 獲取模組顏色
        module_name = record.name.split('.')[-1]
        module_color = MODULE_COLORS.get(module_name, MODULE_COLORS["DEFAULT"])
        
        # 替換級別和模組名稱為彩色版本
        colored_level = f"{level_color}{record.levelname}{Colors.RESET}"
        colored_module = f"{module_color}[{module_name}]{Colors.RESET}"
        
        # 替換原始訊息中的級別和模組名稱
        message = message.replace(f"[{record.name}]", colored_module)
        message = message.replace(record.levelname, colored_level)
        
        # 如果有方法名稱，也加上顏色
        if hasattr(record, 'method_name') and record.method_name:
            method_str = f"[{record.method_name}]"
            colored_method = f"{Colors.BRIGHT_MAGENTA}{method_str}{Colors.RESET}"
            message = message.replace(method_str, colored_method)
        
        return message

def setup_logger(
    name: str, 
    level: str = "info", 
    format_str: Optional[str] = None,
    date_format: Optional[str] = None,
    file_path: Optional[str] = None,
    verbose: bool = False,
    colored: Optional[bool] = None
) -> logging.Logger:
    """
    設置並返回一個日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        level: 日誌級別，可以是 "debug", "info", "warning", "error", "critical"
        format_str: 日誌格式字串，如果為 None 則使用默認格式
        date_format: 日期格式字串，如果為 None 則使用默認格式
        file_path: 日誌檔案路徑，如果為 None 則使用配置中的路徑
        verbose: 是否啟用詳細日誌，如果為 True 則使用 INFO 級別，否則使用 WARNING 級別
        colored: 是否啟用彩色輸出，如果為 None 則使用配置中的設置
        
    Returns:
        logging.Logger: 配置好的日誌記錄器
    """
    # 如果已經創建過該名稱的記錄器，直接返回
    if name in _loggers:
        return _loggers[name]
    
    # 創建新的記錄器
    logger = logging.getLogger(name)
    
    # 根據 verbose 參數設置日誌級別
    if verbose:
        log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
    else:
        log_level = logging.WARNING
    
    logger.setLevel(log_level)
    
    # 如果沒有處理器，添加處理器
    if not logger.handlers:
        # 控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # 設置格式
        fmt = format_str or DEFAULT_FORMAT
        datefmt = date_format or DEFAULT_DATE_FORMAT
        
        # 決定是否使用彩色格式化器
        use_color = colored if colored is not None else _config["colored_output"]
        if use_color:
            formatter = ColoredFormatter(fmt=fmt, datefmt=datefmt)
        else:
            formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
            
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 如果配置了檔案日誌，添加檔案處理器
        if _config["log_to_file"] or file_path:
            file_path = file_path or _config["log_file_path"]
            file_level = LOG_LEVELS.get(_config["log_file_level"].lower(), logging.INFO)
            
            # 確保目錄存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setLevel(file_level)
            file_formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
    
    # 快取記錄器
    _loggers[name] = logger
    
    return logger

def _format_value(value: Any) -> str:
    """格式化值，處理各種類型"""
    if isinstance(value, (dict, list, tuple, set)):
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except:
            return str(value)
    elif isinstance(value, str) and len(value) > _config["max_message_length"] and _config["truncate_long_messages"]:
        return f"{value[:_config['max_message_length']]}... (截斷，共 {len(value)} 字元)"
    else:
        return str(value)

def _should_show_params(params: Dict[str, Any]) -> bool:
    """判斷是否應該顯示參數"""
    if not _config["show_params_once"]:
        return True
    
    # 將參數轉換為可哈希的形式
    param_str = json.dumps(params, sort_keys=True)
    param_hash = hash(param_str)
    
    # 如果參數已經顯示過，返回 False
    if param_hash in _config["params_shown"]:
        return False
    
    # 否則添加到已顯示集合中，返回 True
    _config["params_shown"].add(param_hash)
    return True

def log_message(
    logger: logging.Logger, 
    level: int, 
    message: str, 
    method_name: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    記錄日誌訊息
    
    Args:
        logger: 日誌記錄器
        level: 日誌級別
        message: 日誌訊息
        method_name: 方法名稱，用於標識日誌來源
        params: 參數字典，如果設置了 show_params_once，則只顯示一次
        **kwargs: 其他要記錄的資訊
    """
    # 處理參數
    if params and _should_show_params(params):
        formatted_params = ", ".join(f"{k}={_format_value(v)}" for k, v in params.items() if v is not None)
        if formatted_params:
            message = f"{message} - 參數: {{{formatted_params}}}"
    
    # 添加其他資訊
    if kwargs:
        extra_info = ", ".join(f"{k}={_format_value(v)}" for k, v in kwargs.items())
        message = f"{message} ({extra_info})"
    
    # 創建額外資訊字典
    extra = {}
    if method_name:
        extra["method_name"] = method_name
        prefix = f"[{method_name}] "
        if not message.startswith(prefix):
            message = f"{prefix}{message}"
    
    # 根據級別記錄訊息
    if level == logging.DEBUG:
        logger.debug(message, extra=extra)
    elif level == logging.INFO:
        logger.info(message, extra=extra)
    elif level == logging.WARNING:
        logger.warning(message, extra=extra)
    elif level == logging.ERROR:
        logger.error(message, extra=extra)
    elif level == logging.CRITICAL:
        logger.critical(message, extra=extra)

# 便捷函數
def debug(logger: logging.Logger, message: str, method_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """記錄 DEBUG 級別日誌"""
    log_message(logger, logging.DEBUG, message, method_name, params, **kwargs)

def info(logger: logging.Logger, message: str, method_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """記錄 INFO 級別日誌"""
    log_message(logger, logging.INFO, message, method_name, params, **kwargs)

def warning(logger: logging.Logger, message: str, method_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """記錄 WARNING 級別日誌"""
    log_message(logger, logging.WARNING, message, method_name, params, **kwargs)

def error(logger: logging.Logger, message: str, method_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """記錄 ERROR 級別日誌"""
    log_message(logger, logging.ERROR, message, method_name, params, **kwargs)

def critical(logger: logging.Logger, message: str, method_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """記錄 CRITICAL 級別日誌"""
    log_message(logger, logging.CRITICAL, message, method_name, params, **kwargs)

def log_exception(logger: logging.Logger, e: Exception, method_name: Optional[str] = None) -> None:
    """
    記錄異常資訊
    
    Args:
        logger: 日誌記錄器
        e: 異常物件
        method_name: 方法名稱
    """
    error_message = f"發生異常: {str(e)}"
    error(logger, error_message, method_name)
    error(logger, traceback.format_exc(), method_name)

def log_api_request(logger: logging.Logger, method: str, url: str, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> None:
    """
    記錄 API 請求
    
    Args:
        logger: 日誌記錄器
        method: HTTP 方法
        url: 請求 URL
        params: 查詢參數
        data: 請求數據
    """
    message = f"{method} {url}"
    api_params = {}
    if params:
        api_params["params"] = params
    if data:
        api_params["data"] = data
    
    info(logger, message, "API", api_params)

def log_api_response(logger: logging.Logger, url: str, status_code: int, response_data: Any, execution_time: Optional[float] = None) -> None:
    """
    記錄 API 回應
    
    Args:
        logger: 日誌記錄器
        url: 請求 URL
        status_code: 狀態碼
        response_data: 回應數據
        execution_time: 執行時間（秒）
    """
    message = f"回應: {url} - 狀態碼: {status_code}"
    response_params = {}
    
    if execution_time is not None:
        response_params["execution_time"] = f"{execution_time:.2f}秒"
    
    # 只在 DEBUG 級別記錄完整回應
    if logger.isEnabledFor(logging.DEBUG):
        response_params["data"] = response_data
    
    info(logger, message, "API", response_params)

def reset_params_shown() -> None:
    """重置已顯示參數集合"""
    _config["params_shown"] = set()

def get_logger(name: str) -> logging.Logger:
    """
    獲取已配置的日誌記錄器，如果不存在則創建一個新的
    
    Args:
        name: 日誌記錄器名稱
        
    Returns:
        logging.Logger: 日誌記錄器
    """
    if name in _loggers:
        return _loggers[name]
    else:
        return setup_logger(name)

# 初始化根日誌記錄器
root_logger = setup_logger("root") 