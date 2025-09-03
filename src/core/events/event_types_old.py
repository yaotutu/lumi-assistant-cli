#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件类型定义
定义系统中的所有事件类型，支持统一的事件驱动架构
"""
from dataclasses import dataclass
from typing import Any, Optional, Dict
from abc import ABC, abstractmethod
import time


class BaseEvent(ABC):
    """事件基类"""
    def __init__(self, source: str = "unknown", data: Optional[Dict[str, Any]] = None):
        self.source = source  # 事件来源（cli、grpc、gui等）
        self.timestamp = time.time()  # 事件时间戳
        self.data = data or {}  # 事件数据
        
    @property
    @abstractmethod
    def event_type(self) -> str:
        """事件类型标识"""
        pass


@dataclass
class AudioEvent(BaseEvent):
    """音频相关事件基类"""
    pass


@dataclass 
class StartListeningEvent(AudioEvent):
    """开始录音事件 - 对应CLI的'b'键，GUI的按下按钮，gRPC的StartListening调用"""
    @property
    def event_type(self) -> str:
        return "audio.start_listening"


@dataclass
class StopListeningEvent(AudioEvent):
    """停止录音事件 - 对应CLI的'e'键，GUI的松开按钮，gRPC的StopListening调用"""
    @property
    def event_type(self) -> str:
        return "audio.stop_listening"


@dataclass
class AudioDataEvent(AudioEvent):
    """音频数据事件"""
    audio_data: bytes
    
    @property
    def event_type(self) -> str:
        return "audio.data"


@dataclass
class TextEvent(BaseEvent):
    """文本相关事件基类"""
    pass


@dataclass
class TextInputEvent(TextEvent):
    """文本输入事件"""
    text: str
    
    @property
    def event_type(self) -> str:
        return "text.input"


@dataclass
class ASRResultEvent(TextEvent):
    """ASR识别结果事件"""
    text: str
    confidence: float = 0.0
    
    @property
    def event_type(self) -> str:
        return "text.asr_result"


@dataclass
class LLMResponseEvent(TextEvent):
    """LLM回复事件"""
    text: str
    model: str = ""
    
    @property
    def event_type(self) -> str:
        return "text.llm_response"


@dataclass
class SystemEvent(BaseEvent):
    """系统事件基类"""
    pass


@dataclass
class ShutdownEvent(SystemEvent):
    """系统关闭事件 - 对应CLI的'q'键"""
    @property
    def event_type(self) -> str:
        return "system.shutdown"


@dataclass
class StatusEvent(SystemEvent):
    """状态更新事件"""
    component: str  # 组件名称（asr、llm、tts等）
    status: str     # 状态（ready、busy、error等）
    message: str = ""
    
    @property
    def event_type(self) -> str:
        return "system.status"


@dataclass
class IntentEvent(BaseEvent):
    """意图识别事件"""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    
    @property
    def event_type(self) -> str:
        return "intent.detected"


@dataclass
class ToolCallEvent(BaseEvent):
    """工具调用事件"""
    tool_name: str
    parameters: Dict[str, Any]
    call_id: str = ""
    
    @property
    def event_type(self) -> str:
        return "tool.call"


@dataclass
class ToolResultEvent(BaseEvent):
    """工具调用结果事件"""
    tool_name: str
    result: Any
    call_id: str = ""
    success: bool = True
    error: str = ""
    
    @property
    def event_type(self) -> str:
        return "tool.result"


@dataclass 
class AudioDataEvent(AudioEvent):
    """音频数据事件"""
    audio_data: bytes
    format: str = "pcm"
    duration: float = 0.0
    
    @property
    def event_type(self) -> str:
        return "audio.data"


@dataclass
class PlayAudioEvent(AudioEvent):
    """播放音频事件"""
    audio_data: bytes
    format: str = "pcm"
    blocking: bool = True
    
    @property
    def event_type(self) -> str:
        return "audio.play"