#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版LLM处理器
支持对话管理、流式输出、思维过滤等高级功能
"""

import re
import yaml
from typing import AsyncGenerator, Optional, List, Dict, Any
from pathlib import Path

from .openai_llm import OpenAILLM
from ..dialogue.dialogue_manager import DialogueManager


class EnhancedLLM(OpenAILLM):
    """增强的OpenAI LLM - 集成对话管理和人性化功能"""
    
    def __init__(self, config: Dict[str, Any], personality_config_path: str = "config/personality.yaml"):
        """
        初始化增强LLM
        
        Args:
            config: LLM配置
            personality_config_path: 人物性格配置文件路径
        """
        super().__init__(config)
        
        # 加载人物性格配置
        self.personality_config = self._load_personality_config(personality_config_path)
        
        # 初始化对话管理器
        self.dialogue_manager = DialogueManager(self.personality_config.get("lumi", {}))
        
        # 思维过滤状态
        self.thinking_active = False
        self.thinking_buffer = ""
    
    def _load_personality_config(self, config_path: str) -> dict:
        """
        加载人物性格配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        else:
            print(f"⚠️ 人物配置文件不存在: {config_path}，使用默认配置")
            return {}
    
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        流式对话接口，支持思维过滤
        
        Args:
            message: 用户消息
            
        Yields:
            过滤后的响应片段
        """
        # 添加用户消息到对话历史
        self.dialogue_manager.add_message("user", message)
        
        # 获取完整的对话上下文（包含系统提示词）
        messages = self.dialogue_manager.get_llm_dialogue()
        
        try:
            # 调用OpenAI流式API
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            full_response = ""
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    
                    # 过滤思维标签
                    filtered_content = self._filter_thinking(content)
                    
                    if filtered_content:
                        full_response += filtered_content
                        yield filtered_content
            
            # 保存助手回复到对话历史
            if full_response:
                self.dialogue_manager.add_message("assistant", full_response)
            
        except Exception as e:
            error_msg = f"抱歉，我遇到了一点问题：{str(e)}"
            print(f"❌ LLM错误: {e}")
            self.dialogue_manager.add_message("assistant", error_msg)
            yield error_msg
    
    def _filter_thinking(self, content: str) -> str:
        """
        过滤思维标签内容（参考xiaozhi实现）
        
        Args:
            content: 原始内容片段
            
        Returns:
            过滤后的内容
        """
        # 将内容添加到缓冲区
        self.thinking_buffer += content
        filtered = ""
        
        # 检查是否有完整的标签
        while True:
            if not self.thinking_active:
                # 查找<think>标签开始
                think_start = self.thinking_buffer.find("<think>")
                if think_start != -1:
                    # 输出标签前的内容
                    filtered += self.thinking_buffer[:think_start]
                    self.thinking_buffer = self.thinking_buffer[think_start + 7:]
                    self.thinking_active = True
                else:
                    # 检查是否可能是不完整的标签开始
                    if self.thinking_buffer.endswith("<") or \
                       self.thinking_buffer.endswith("<t") or \
                       self.thinking_buffer.endswith("<th") or \
                       self.thinking_buffer.endswith("<thi") or \
                       self.thinking_buffer.endswith("<thin"):
                        # 保留可能的标签开始，不输出
                        break
                    else:
                        # 输出所有内容
                        filtered += self.thinking_buffer
                        self.thinking_buffer = ""
                        break
            else:
                # 查找</think>标签结束
                think_end = self.thinking_buffer.find("</think>")
                if think_end != -1:
                    # 跳过思维内容，继续处理标签后的内容
                    self.thinking_buffer = self.thinking_buffer[think_end + 8:]
                    self.thinking_active = False
                else:
                    # 在思维模式中，不输出任何内容
                    break
        
        return filtered
    
    async def chat(self, message: str) -> str:
        """
        非流式对话（收集完整响应）
        
        Args:
            message: 用户消息
            
        Returns:
            完整的响应
        """
        full_response = ""
        async for chunk in self.chat_stream(message):
            full_response += chunk
        return full_response
    
    # 会话管理方法
    async def new_session(self):
        """创建新会话"""
        await self.dialogue_manager.start_new_session()
        self.thinking_active = False
        self.thinking_buffer = ""
    
    async def resume_session(self, session_id: str) -> bool:
        """恢复会话"""
        return await self.dialogue_manager.resume_session(session_id)
    
    async def list_sessions(self, limit: int = 10) -> List[dict]:
        """列出历史会话"""
        return await self.dialogue_manager.list_sessions(limit)
    
    async def export_session(self, session_id: str = None) -> Optional[dict]:
        """导出会话"""
        return await self.dialogue_manager.export_session(session_id)
    
    async def clear_session(self):
        """清空当前会话"""
        await self.dialogue_manager.clear_current_session()
        self.thinking_active = False
        self.thinking_buffer = ""
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        return await self.dialogue_manager.delete_session(session_id)
    
    def get_current_session_info(self) -> Optional[dict]:
        """获取当前会话信息"""
        session = self.dialogue_manager.get_current_session()
        if session:
            return {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "message_count": len(session.messages),
                "title": session.metadata.get("title", "新对话")
            }
        return None
    
    async def initialize(self) -> bool:
        """
        初始化（创建或恢复会话）
        
        Returns:
            是否初始化成功
        """
        try:
            # 检查是否有历史会话
            sessions = await self.list_sessions(1)
            
            if sessions and len(sessions) > 0:
                # 有历史会话，询问是否恢复
                latest = sessions[0]
                print(f"\n💬 发现上次会话: {latest['title']}")
                print("是否继续上次对话？(y/n): ", end="", flush=True)
                
                import sys
                if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                    choice = input().strip().lower()
                else:
                    # 非交互模式，自动创建新会话
                    choice = 'n'
                
                if choice == 'y':
                    success = await self.resume_session(latest['session_id'])
                    if success:
                        print("✅ 已恢复上次会话")
                        
                        # 显示最近的对话
                        session = self.dialogue_manager.get_current_session()
                        if session and session.messages:
                            print("\n最近对话：")
                            for msg in session.messages[-4:]:  # 最近2轮
                                role = "👤 你" if msg.role == "user" else "🤖 Lumi"
                                content = msg.content[:80] + ("..." if len(msg.content) > 80 else "")
                                print(f"{role}: {content}")
                            print()
                    else:
                        print("⚠️ 恢复失败，创建新会话")
                        await self.new_session()
                else:
                    await self.new_session()
                    print("✅ 已创建新会话")
            else:
                # 没有历史会话，创建新的
                await self.new_session()
                print("✅ 已创建新会话")
            
            return True
            
        except Exception as e:
            print(f"❌ 会话初始化失败: {e}")
            return False
    
    async def close(self):
        """关闭时保存会话"""
        try:
            # 保存当前会话
            await self.dialogue_manager._save_session()
            # 调用父类的关闭方法
            await super().close()
        except Exception as e:
            print(f"关闭EnhancedLLM时出错: {e}")