#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话管理器
管理对话上下文、系统提示词、记忆等
"""

import re
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from .session_manager import SessionManager, Session
from .message import Message


class DialogueManager:
    """对话管理器 - 整合会话管理和上下文构建"""
    
    def __init__(self, personality_config: Optional[dict] = None):
        """
        初始化对话管理器
        
        Args:
            personality_config: 人物性格配置
        """
        self.personality_config = personality_config or {}
        self.session_manager = SessionManager()
        self.memory_interface = None  # 预留记忆接口
        
        # 当前会话的上下文信息（从对话中提取）
        self.session_context = {}
    
    async def start_new_session(self) -> Session:
        """开始新会话"""
        session = await self.session_manager.create_session()
        self.session_context = {}  # 清空上下文
        return session
    
    async def resume_session(self, session_id: str) -> bool:
        """
        恢复会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功恢复
        """
        session = await self.session_manager.load_session(session_id)
        if session:
            # 从会话元数据恢复上下文
            self.session_context = session.metadata.get("context", {})
            return True
        return False
    
    def add_message(self, role: str, content: str):
        """
        添加消息到当前会话
        
        Args:
            role: 角色（user/assistant/system）
            content: 消息内容
        """
        session = self.session_manager.get_current_session()
        if not session:
            print("⚠️ 没有活动会话，请先创建会话")
            return
        
        # 创建并添加消息
        message = Message(role, content)
        session.add_message(message)
        
        # 提取上下文信息
        if role == "user":
            self._extract_context(content)
        
        # 异步保存会话（不阻塞）
        asyncio.create_task(self._save_session())
    
    async def _save_session(self):
        """异步保存会话"""
        try:
            # 更新会话元数据中的上下文
            session = self.session_manager.get_current_session()
            if session:
                session.metadata["context"] = self.session_context
                await self.session_manager.save_current_session()
        except Exception as e:
            print(f"⚠️ 保存会话时出错: {e}")
    
    def _extract_context(self, content: str):
        """
        从用户输入提取关键信息
        
        Args:
            content: 用户输入内容
        """
        # 提取用户名字
        name_patterns = [
            r"我叫(.+?)[\s，。！]",
            r"我是(.+?)[\s，。！]", 
            r"叫我(.+?)[\s，。！]",
            r"我的名字是(.+?)[\s，。！]"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, content + "。")  # 添加句号确保匹配
            if match:
                name = match.group(1).strip()
                if len(name) <= 10:  # 合理的名字长度
                    self.session_context["user_name"] = name
                    print(f"💡 识别到用户名字: {name}")
                    break
        
        # 提取用户偏好
        if "喜欢" in content:
            match = re.search(r"喜欢(.+?)[\s，。！]", content + "。")
            if match:
                preference = match.group(1).strip()
                if "preferences" not in self.session_context:
                    self.session_context["preferences"] = []
                if preference not in self.session_context["preferences"]:
                    self.session_context["preferences"].append(preference)
                    print(f"💡 识别到用户偏好: {preference}")
        
        # 提取位置信息
        location_patterns = [
            r"我在(.+?)[\s，。！]",
            r"我住在(.+?)[\s，。！]",
            r"来自(.+?)[\s，。！]"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content + "。")
            if match:
                location = match.group(1).strip()
                if len(location) <= 20:
                    self.session_context["location"] = location
                    print(f"💡 识别到位置信息: {location}")
                    break
    
    def get_llm_dialogue(self) -> List[Dict[str, str]]:
        """
        获取用于LLM的对话历史（带系统提示词）
        
        Returns:
            消息列表，包含系统提示词和历史对话
        """
        # 构建系统提示词
        system_prompt = self._build_system_prompt()
        
        # 组装消息列表
        messages = [{"role": "system", "content": system_prompt}]
        
        # 获取当前会话的消息
        session = self.session_manager.get_current_session()
        if session:
            # 获取限制数量的消息（避免上下文过长）
            session_messages = session.get_messages_for_llm(limit=20)
            messages.extend(session_messages)
        
        return messages
    
    def _build_system_prompt(self) -> str:
        """
        构建动态系统提示词
        
        Returns:
            系统提示词
        """
        # 获取基础提示词
        base_prompt = self.personality_config.get("base_prompt", self._get_default_prompt())
        
        # 时间处理
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M")
        hour = now.hour
        
        # 时间问候
        time_greeting = self._get_time_greeting(hour)
        
        # 构建会话上下文摘要
        context_summary = self._build_context_summary()
        
        # 替换占位符
        prompt = base_prompt.replace("{{current_time}}", current_time)
        prompt = prompt.replace("{{time_greeting}}", time_greeting)
        prompt = prompt.replace("{{session_context}}", context_summary)
        
        return prompt
    
    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是Lumi，一个友善、活泼的AI助手。当前时间：{{current_time}}

【性格特点】
- 友善活泼，像朋友而非机器
- 用轻松自然的口语化表达
- 回复简洁有温度，避免长篇大论

【对话原则】
- 永远不说"作为AI助手"这类机械化表达
- 根据时间调整问候
- 记住对话中的信息并自然引用
- 适时表达关心和情感

{{time_greeting}}

<memory>
{{session_context}}
</memory>

<think>
内部思考区域，分析用户情绪和需求，但不输出给用户
</think>"""
    
    def _get_time_greeting(self, hour: int) -> str:
        """
        获取时间问候语
        
        Args:
            hour: 当前小时
            
        Returns:
            时间问候语
        """
        greetings = self.personality_config.get("time_greetings", {})
        
        if 5 <= hour < 12:
            return greetings.get("morning", "早上好，新的一天开始了～")
        elif 12 <= hour < 14:
            return greetings.get("noon", "中午了，记得吃午饭哦～")
        elif 14 <= hour < 18:
            return greetings.get("afternoon", "下午好，要不要喝杯咖啡提提神？")
        elif 18 <= hour < 22:
            return greetings.get("evening", "晚上好，今天过得怎么样？")
        else:
            return greetings.get("night", "夜深了，记得早点休息哦～")
    
    def _build_context_summary(self) -> str:
        """
        构建会话上下文摘要
        
        Returns:
            上下文摘要文本
        """
        if not self.session_context:
            return "这是我们的第一次对话，很高兴认识你！"
        
        summary_parts = []
        
        # 添加用户名字
        if "user_name" in self.session_context:
            summary_parts.append(f"用户名字：{self.session_context['user_name']}")
        
        # 添加位置信息
        if "location" in self.session_context:
            summary_parts.append(f"用户位置：{self.session_context['location']}")
        
        # 添加偏好
        if "preferences" in self.session_context:
            prefs = self.session_context['preferences'][:5]  # 最多5个
            summary_parts.append(f"用户喜好：{', '.join(prefs)}")
        
        return "\n".join(summary_parts) if summary_parts else "正在了解用户中..."
    
    # 预留的记忆接口
    async def load_memory(self, user_id: str) -> Optional[dict]:
        """
        加载长期记忆（预留接口）
        
        Args:
            user_id: 用户ID
            
        Returns:
            记忆数据
        """
        if self.memory_interface:
            return await self.memory_interface.load(user_id)
        return None
    
    async def save_memory(self, user_id: str):
        """
        保存长期记忆（预留接口）
        
        Args:
            user_id: 用户ID
        """
        if self.memory_interface:
            await self.memory_interface.save(user_id, self.session_context)
    
    # 会话管理快捷方法
    async def list_sessions(self, limit: int = 10) -> List[dict]:
        """列出最近的会话"""
        return await self.session_manager.list_sessions(limit)
    
    async def clear_current_session(self):
        """清空当前会话"""
        await self.session_manager.clear_current_session()
        self.session_context = {}
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        return await self.session_manager.delete_session(session_id)
    
    async def export_session(self, session_id: str = None) -> Optional[dict]:
        """导出会话"""
        return await self.session_manager.export_session(session_id)
    
    def get_current_session(self) -> Optional[Session]:
        """获取当前会话"""
        return self.session_manager.get_current_session()