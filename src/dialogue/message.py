#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
消息实体定义
"""

from datetime import datetime
from typing import Optional, Dict, Any


class Message:
    """消息实体类"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        """
        初始化消息
        
        Args:
            role: 角色（user/assistant/system）
            content: 消息内容
            timestamp: 时间戳（可选）
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息"""
        timestamp = None
        if data.get("timestamp"):
            timestamp = datetime.fromisoformat(data["timestamp"])
        
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp
        )
    
    def __repr__(self) -> str:
        return f"Message(role='{self.role}', content='{self.content[:50]}...')"