#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM抽象基类
定义大语言模型的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class LLMProviderBase(ABC):
    """LLM提供者基类"""
    
    @abstractmethod
    async def chat(self, message: str, history: Optional[List[Dict]] = None) -> Optional[str]:
        """
        对话聊天接口
        
        Args:
            message: 用户消息
            history: 对话历史，格式为[{"role": "user/assistant", "content": "..."}]
            
        Returns:
            LLM回复内容，失败返回None
        """
        pass
    
    @abstractmethod
    async def chat_with_tools(self, message: str, tools: List[Dict], history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        支持工具调用的对话接口
        
        Args:
            message: 用户消息
            tools: 可用工具列表
            history: 对话历史
            
        Returns:
            包含回复和工具调用信息的字典
        """
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """检查是否准备就绪"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """测试连接是否正常"""
        pass