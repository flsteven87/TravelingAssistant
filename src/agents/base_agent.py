from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
import os
from dotenv import load_dotenv
from ..utils import logging_utils

# 載入環境變數
load_dotenv()

class BaseAgent(ABC):
    """
    基礎 Agent 類別，所有專業 Agent 都應繼承此類別
    提供基本的任務處理和通信功能
    """
    
    def __init__(
        self, 
        name: str, 
        role: str,
        goal: str,
        backstory: str = "",
        description: str = "", 
        api_key: Optional[str] = None,
        llm: str = "gpt-4o-mini",
        verbose: bool = False,
        memory: bool = True,
        allow_delegation: bool = False,
        max_iter: int = 15
    ):
        """
        初始化 Agent
        
        Args:
            name: Agent 的名稱
            role: Agent 的角色
            goal: Agent 的目標
            backstory: Agent 的背景故事
            description: Agent 的描述，說明其功能和職責
            api_key: API 金鑰，用於外部服務調用
            llm: 使用的語言模型
            verbose: 是否輸出詳細日誌
            memory: 是否啟用記憶功能
            allow_delegation: 是否允許委派任務給其他 Agent
            max_iter: 最大迭代次數
        """
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.description = description
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.travel_api_key = os.getenv("TRAVEL_API_KEY", "DhDkXZkGXaYBZhkk1Z9m9BuZDJGy")  # 默認使用題目提供的 API Key
        self.llm = llm
        self.verbose = verbose
        self.memory = memory
        self.allow_delegation = allow_delegation
        self.max_iter = max_iter
        self.tools: List[Callable] = []  # Agent 可用的工具函數列表
        self.memory_store: Dict[str, Any] = {}  # Agent 的記憶/狀態存儲
        self.collaborators: List['BaseAgent'] = []  # 協作 Agent 列表
        
        # 初始化日誌記錄器
        self.logger = logging_utils.setup_logger(name=self.name, verbose=self.verbose)
        
    def add_tool(self, tool: Callable) -> None:
        """
        為 Agent 添加工具函數
        
        Args:
            tool: 工具函數，Agent 可以調用它來完成特定任務
        """
        self.tools.append(tool)
        logging_utils.debug(self.logger, f"添加工具: {tool.__name__}", "add_tool")
    
    def add_tools(self, tools: List[Callable]) -> None:
        """
        為 Agent 批量添加工具函數
        
        Args:
            tools: 工具函數列表
        """
        self.tools.extend(tools)
        tool_names = [tool.__name__ for tool in tools]
        logging_utils.debug(self.logger, f"批量添加工具: {tool_names}", "add_tools")
    
    def add_collaborator(self, agent: 'BaseAgent') -> None:
        """
        添加協作 Agent
        
        Args:
            agent: 協作的 Agent
        """
        self.collaborators.append(agent)
        logging_utils.info(self.logger, f"添加協作者: {agent.name} ({agent.role})", "add_collaborator")
    
    def remember(self, key: str, value: Any) -> None:
        """
        記住某個信息
        
        Args:
            key: 信息的鍵
            value: 信息的值
        """
        self.memory_store[key] = value
        logging_utils.info(self.logger, f"記住了: {key}", "remember", 
                          {"value_type": type(value).__name__})
    
    def recall(self, key: str, default: Any = None) -> Any:
        """
        回憶某個信息
        
        Args:
            key: 信息的鍵
            default: 如果信息不存在，返回的默認值
            
        Returns:
            記憶中的信息
        """
        value = self.memory_store.get(key, default)
        if key in self.memory_store:
            logging_utils.info(self.logger, f"回憶起: {key}", "recall", 
                              {"value_type": type(value).__name__})
        return value
    
    def clear_memory(self) -> None:
        """
        清除所有記憶
        """
        memory_count = len(self.memory_store)
        self.memory_store.clear()
        logging_utils.info(self.logger, f"清除了所有記憶", "clear_memory", 
                          {"memory_count": memory_count})
    
    @abstractmethod
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行任務的抽象方法，所有子類都必須實現
        
        Args:
            task: 任務數據，包含任務的描述、參數等
            
        Returns:
            任務執行結果
        """
        pass
    
    def _use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        使用指定的工具
        
        Args:
            tool_name: 工具名稱
            **kwargs: 傳遞給工具的參數
            
        Returns:
            工具執行結果
            
        Raises:
            ValueError: 如果找不到指定的工具
        """
        for tool in self.tools:
            if tool.__name__ == tool_name:
                logging_utils.info(self.logger, f"正在使用工具: {tool_name}", "_use_tool", 
                                  {"params": kwargs})
                return tool(**kwargs)
        
        error_msg = f"Tool '{tool_name}' not found"
        logging_utils.error(self.logger, error_msg, "_use_tool")
        raise ValueError(error_msg)
    
    def collaborate(self, agent: 'BaseAgent', task: Dict[str, Any]) -> Dict[str, Any]:
        """
        與另一個 Agent 協作
        
        Args:
            agent: 協作的 Agent
            task: 協作任務
            
        Returns:
            協作結果
        """
        logging_utils.info(self.logger, f"正在與 {agent.name} 協作處理任務", "collaborate", 
                          {"task_type": task.get("type", "unknown")})
        return agent.execute_task(task)
    
    def get_system_prompt(self) -> str:
        """
        獲取系統提示詞
        
        Returns:
            系統提示詞
        """
        return f"""
        你是 {self.name}，一個 {self.role}。
        
        你的目標是: {self.goal}
        
        背景: {self.backstory}
        
        請記住你的角色和目標，並根據用戶的需求提供專業的建議和服務。
        """
    
    def __str__(self) -> str:
        """
        返回 Agent 的字符串表示
        
        Returns:
            Agent 的字符串表示
        """
        return f"{self.name} ({self.role}): {self.description}" 