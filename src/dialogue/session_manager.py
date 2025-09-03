#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会话管理器
管理会话的创建、保存、加载、删除等操作
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
from asyncio import Lock
from .message import Message


class Session:
    """会话实体"""
    
    def __init__(self, session_id: str = None):
        """初始化会话"""
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.messages: List[Message] = []
        self.metadata = {
            "title": None,
            "user_name": None,
            "context": {}
        }
    
    def add_message(self, message: Message):
        """添加消息到会话"""
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # 自动生成标题（从第一条用户消息）
        if not self.metadata["title"] and message.role == "user":
            content = message.content
            self.metadata["title"] = content[:30] + ("..." if len(content) > 30 else "")
    
    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        """从字典反序列化"""
        session = cls(data["session_id"])
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        session.messages = [Message.from_dict(msg) for msg in data["messages"]]
        session.metadata = data["metadata"]
        return session
    
    def get_messages_for_llm(self, limit: int = 20) -> List[Dict]:
        """获取用于LLM的消息格式（限制数量）"""
        # 只返回最近的消息，避免上下文过长
        recent_messages = self.messages[-limit:] if len(self.messages) > limit else self.messages
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
            if msg.role in ["user", "assistant"]  # 不包含系统消息
        ]


class SessionManager:
    """会话管理器"""
    
    def __init__(self, storage_path: str = "data/sessions"):
        """
        初始化会话管理器
        
        Args:
            storage_path: 会话存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.current_session: Optional[Session] = None
        self.sessions: Dict[str, Session] = {}  # 内存缓存
        self._lock = Lock()
        
        # 加载会话索引
        self._load_sessions_index()
    
    def _load_sessions_index(self):
        """加载会话索引"""
        index_file = self.storage_path / "sessions_index.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                self.sessions_index = json.load(f)
        else:
            self.sessions_index = []
    
    def _save_sessions_index(self):
        """保存会话索引"""
        index_file = self.storage_path / "sessions_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self.sessions_index, f, ensure_ascii=False, indent=2)
    
    async def create_session(self) -> Session:
        """创建新会话"""
        async with self._lock:
            session = Session()
            self.current_session = session
            self.sessions[session.session_id] = session
            
            # 更新索引
            self.sessions_index.insert(0, {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "title": "新对话",
                "preview": ""
            })
            self._save_sessions_index()
            
            print(f"📝 新会话已创建: {session.session_id[:8]}...")
            return session
    
    async def load_session(self, session_id: str) -> Optional[Session]:
        """加载指定会话"""
        async with self._lock:
            # 先从内存缓存查找
            if session_id in self.sessions:
                self.current_session = self.sessions[session_id]
                return self.current_session
            
            # 从文件加载
            session_file = self.storage_path / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    session = Session.from_dict(data)
                    self.sessions[session_id] = session
                    self.current_session = session
                    print(f"📂 会话已加载: {session_id[:8]}...")
                    return session
            
            return None
    
    async def save_current_session(self):
        """保存当前会话"""
        if not self.current_session:
            return
        
        async with self._lock:
            # 保存会话数据
            session_file = self.storage_path / f"{self.current_session.session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_session.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self._update_session_index()
    
    def _update_session_index(self):
        """更新会话索引信息"""
        if not self.current_session:
            return
        
        # 获取会话标题和预览
        title = self.current_session.metadata.get("title", "新对话")
        preview = ""
        
        for msg in self.current_session.messages:
            if msg.role == "user":
                preview = msg.content[:50] + ("..." if len(msg.content) > 50 else "")
                break
        
        # 查找并更新或添加
        session_info = {
            "session_id": self.current_session.session_id,
            "created_at": self.current_session.created_at.isoformat(),
            "updated_at": self.current_session.updated_at.isoformat(),
            "title": title,
            "preview": preview
        }
        
        # 更新或插入
        updated = False
        for i, item in enumerate(self.sessions_index):
            if item["session_id"] == self.current_session.session_id:
                self.sessions_index[i] = session_info
                updated = True
                break
        
        if not updated:
            self.sessions_index.insert(0, session_info)
        
        # 限制索引数量（最多保留100个）
        self.sessions_index = self.sessions_index[:100]
        
        self._save_sessions_index()
    
    async def list_sessions(self, limit: int = 10) -> List[dict]:
        """列出最近的会话"""
        return self.sessions_index[:limit]
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        async with self._lock:
            # 从内存删除
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            # 删除文件
            session_file = self.storage_path / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            # 更新索引
            self.sessions_index = [
                s for s in self.sessions_index 
                if s["session_id"] != session_id
            ]
            self._save_sessions_index()
            
            # 如果删除的是当前会话，清空
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
            
            return True
    
    async def clear_current_session(self):
        """清空当前会话的消息"""
        if self.current_session:
            self.current_session.messages.clear()
            self.current_session.metadata["context"] = {}
            await self.save_current_session()
    
    def get_current_session(self) -> Optional[Session]:
        """获取当前会话"""
        return self.current_session
    
    async def export_session(self, session_id: str = None) -> Optional[dict]:
        """导出会话数据"""
        if session_id:
            session = await self.load_session(session_id)
        else:
            session = self.current_session
        
        if session:
            return session.to_dict()
        return None