#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenAI LLM提供者实现
支持OpenAI兼容的API接口
"""

import asyncio
import json
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI
from .base import LLMProviderBase


class OpenAILLM(LLMProviderBase):
    """OpenAI LLM提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化OpenAI LLM客户端
        
        Args:
            config: 配置字典，包含api_key、base_url、model等
        """
        self.config = config
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.7)
        
        # 初始化异步OpenAI客户端，禁用代理避免SOCKS问题
        import httpx
        
        # 创建自定义HTTP客户端，禁用环境变量代理设置
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),  # 设置超时时间
            trust_env=False  # 禁用环境变量代理设置
        )
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=http_client
        )
        
        # 连接状态标记
        self._is_ready = False
        
    async def chat(self, message: str, history: Optional[List[Dict]] = None) -> Optional[str]:
        """
        对话聊天接口
        
        Args:
            message: 用户消息
            history: 对话历史，格式为[{"role": "user/assistant", "content": "..."}]
            
        Returns:
            LLM回复内容，失败返回None
        """
        try:
            # 构建消息列表
            messages = []
            
            # 添加历史对话
            if history:
                messages.extend(history)
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": message})
            
            # 调用OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # 提取回复内容
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            
            return None
            
        except Exception as e:
            print(f"OpenAI API调用失败: {str(e)}")
            return None
    
    async def chat_with_tools(self, message: str, tools: List[Dict], history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        支持工具调用的对话接口
        
        Args:
            message: 用户消息
            tools: 可用工具列表，OpenAI函数调用格式
            history: 对话历史
            
        Returns:
            包含回复和工具调用信息的字典
        """
        try:
            # 构建消息列表
            messages = []
            
            # 添加历史对话
            if history:
                messages.extend(history)
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": message})
            
            # 调用OpenAI API，支持函数调用
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",  # 让模型自动决定是否调用工具
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # 解析响应
            result = {
                "content": None,
                "tool_calls": [],
                "finish_reason": None
            }
            
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                result["finish_reason"] = choice.finish_reason
                
                # 获取文本回复
                if choice.message.content:
                    result["content"] = choice.message.content
                
                # 获取工具调用
                if choice.message.tool_calls:
                    for tool_call in choice.message.tool_calls:
                        result["tool_calls"].append({
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        })
            
            return result
            
        except Exception as e:
            print(f"OpenAI API工具调用失败: {str(e)}")
            return {
                "content": None,
                "tool_calls": [],
                "error": str(e)
            }
    
    def is_ready(self) -> bool:
        """检查是否准备就绪"""
        return self._is_ready and bool(self.api_key)
    
    async def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            # 发送一个简单的测试请求
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            if response.choices and len(response.choices) > 0:
                self._is_ready = True
                return True
            
            return False
            
        except Exception as e:
            print(f"OpenAI连接测试失败: {str(e)}")
            self._is_ready = False
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "OpenAI",
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
    
    async def close(self):
        """关闭客户端，释放资源"""
        try:
            if hasattr(self, 'client') and self.client:
                await self.client.close()
        except Exception as e:
            print(f"关闭OpenAI客户端时出错: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器进入"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()