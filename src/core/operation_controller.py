#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作控制器
提供统一的操作接口，支持CLI、gRPC、GUI等多种触发方式
"""
from .events.event_bus import event_bus
from .events.event_types import (
    StartListeningEvent, StopListeningEvent, 
    ShutdownEvent, TextInputEvent, StatusEvent
)


class OperationController:
    """
    操作控制器 - 统一的操作接口
    将用户操作抽象为标准接口，支持多种触发方式
    """
    
    def __init__(self):
        self.is_listening = False
        self.is_shutdown = False
    
    async def start_listening(self, source: str = "unknown") -> None:
        """
        开始录音
        - CLI: 按下 'b' 键触发
        - gRPC: StartListening() 调用触发
        - GUI: 按下按钮触发
        
        Args:
            source: 触发源标识（cli、grpc、gui等）
        """
        if self.is_listening:
            print("⚠️ 已经在录音中...")
            return
            
        self.is_listening = True
        
        # 发布开始录音事件
        event = StartListeningEvent(source=source)
        await event_bus.publish(event)
        
        # 发布状态更新事件
        status_event = StatusEvent(
            source=source,
            component="audio",
            status="listening",
            message="开始录音"
        )
        await event_bus.publish(status_event)
    
    async def stop_listening(self, source: str = "unknown") -> None:
        """
        停止录音
        - CLI: 按下 'e' 键触发
        - gRPC: StopListening() 调用触发  
        - GUI: 松开按钮触发
        
        Args:
            source: 触发源标识（cli、grpc、gui等）
        """
        if not self.is_listening:
            print("⚠️ 当前没有在录音...")
            return
            
        self.is_listening = False
        
        # 发布停止录音事件
        event = StopListeningEvent(source=source)
        await event_bus.publish(event)
        
        # 发布状态更新事件
        status_event = StatusEvent(
            source=source,
            component="audio", 
            status="idle",
            message="停止录音"
        )
        await event_bus.publish(status_event)
    
    async def send_text(self, text: str, source: str = "unknown") -> None:
        """
        发送文本输入
        - CLI: 直接文本输入
        - gRPC: SendText() 调用触发
        - GUI: 文本框输入触发
        
        Args:
            text: 输入的文本
            source: 触发源标识
        """
        if not text.strip():
            return
            
        # 发布文本输入事件
        event = TextInputEvent(source=source, text=text.strip())
        await event_bus.publish(event)
    
    async def shutdown(self, source: str = "unknown") -> None:
        """
        关闭系统
        - CLI: 按下 'q' 键触发
        - gRPC: Shutdown() 调用触发
        - GUI: 关闭窗口触发
        
        Args:
            source: 触发源标识
        """
        if self.is_shutdown:
            return
            
        self.is_shutdown = True
        
        # 发布关闭事件
        event = ShutdownEvent(source=source)
        await event_bus.publish(event)
        
        # 发布状态更新事件
        status_event = StatusEvent(
            source=source,
            component="system",
            status="shutdown",
            message="系统关闭"
        )
        await event_bus.publish(status_event)
    
    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "is_listening": self.is_listening,
            "is_shutdown": self.is_shutdown
        }


# 全局操作控制器实例
operation_controller = OperationController()