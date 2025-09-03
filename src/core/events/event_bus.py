#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件总线
实现发布-订阅模式，支持事件的发布、订阅和处理
"""
import asyncio
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
import logging
from .event_types import BaseEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    事件总线 - 系统核心组件
    负责事件的发布、订阅和分发
    """
    
    def __init__(self):
        # 事件订阅者字典 {event_type: [handlers]}
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        # 通配符订阅者 {pattern: [handlers]}
        self._wildcard_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        # 一次性订阅者
        self._once_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        # 事件历史记录（用于调试）
        self._event_history: List[BaseEvent] = []
        self._max_history = 100
        
    def subscribe(self, event_type: str, handler: Callable[[BaseEvent], Any]) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型，支持通配符（如 "audio.*"）
            handler: 事件处理函数，可以是同步或异步函数
        """
        if '*' in event_type:
            self._wildcard_subscribers[event_type].append(handler)
            logger.debug(f"订阅通配符事件: {event_type} -> {handler.__name__}")
        else:
            self._subscribers[event_type].append(handler)
            logger.debug(f"订阅事件: {event_type} -> {handler.__name__}")
    
    def subscribe_once(self, event_type: str, handler: Callable[[BaseEvent], Any]) -> None:
        """
        订阅事件（一次性）
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        self._once_subscribers[event_type].append(handler)
        logger.debug(f"订阅一次性事件: {event_type} -> {handler.__name__}")
    
    def unsubscribe(self, event_type: str, handler: Callable[[BaseEvent], Any]) -> None:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 要取消的事件处理函数
        """
        if '*' in event_type and handler in self._wildcard_subscribers[event_type]:
            self._wildcard_subscribers[event_type].remove(handler)
        elif handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
        elif handler in self._once_subscribers[event_type]:
            self._once_subscribers[event_type].remove(handler)
            
        logger.debug(f"取消订阅事件: {event_type} -> {handler.__name__}")
    
    async def publish(self, event: BaseEvent) -> None:
        """
        发布事件
        
        Args:
            event: 要发布的事件对象
        """
        event_type = event.event_type
        logger.debug(f"发布事件: {event_type} from {event.source}")
        
        # 记录事件历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # 收集所有匹配的处理器
        handlers = []
        
        # 精确匹配的订阅者
        handlers.extend(self._subscribers.get(event_type, []))
        
        # 通配符匹配的订阅者
        for pattern in self._wildcard_subscribers:
            if self._match_pattern(pattern, event_type):
                handlers.extend(self._wildcard_subscribers[pattern])
        
        # 一次性订阅者
        once_handlers = self._once_subscribers.get(event_type, [])
        handlers.extend(once_handlers)
        
        # 清空一次性订阅者
        if once_handlers:
            self._once_subscribers[event_type].clear()
        
        # 异步执行所有处理器
        if handlers:
            await self._execute_handlers(handlers, event)
        else:
            logger.debug(f"没有找到事件 {event_type} 的处理器")
    
    def publish_sync(self, event: BaseEvent) -> None:
        """
        同步发布事件（在事件循环外使用）
        
        Args:
            event: 要发布的事件对象
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务
                asyncio.create_task(self.publish(event))
            else:
                # 如果没有运行中的事件循环，直接运行
                loop.run_until_complete(self.publish(event))
        except RuntimeError:
            # 没有事件循环，创建新的
            asyncio.run(self.publish(event))
    
    async def _execute_handlers(self, handlers: List[Callable], event: BaseEvent) -> None:
        """执行所有事件处理器"""
        tasks = []
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    # 异步处理器
                    tasks.append(handler(event))
                else:
                    # 同步处理器，在线程池中执行
                    loop = asyncio.get_event_loop()
                    tasks.append(loop.run_in_executor(None, handler, event))
            except Exception as e:
                logger.error(f"事件处理器 {handler.__name__} 执行失败: {e}")
        
        # 等待所有处理器完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _match_pattern(self, pattern: str, event_type: str) -> bool:
        """匹配通配符模式"""
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return event_type.startswith(prefix)
        return pattern == event_type
    
    def get_subscribers_count(self, event_type: str) -> int:
        """获取指定事件类型的订阅者数量"""
        count = len(self._subscribers.get(event_type, []))
        count += len(self._once_subscribers.get(event_type, []))
        
        # 检查通配符匹配
        for pattern in self._wildcard_subscribers:
            if self._match_pattern(pattern, event_type):
                count += len(self._wildcard_subscribers[pattern])
        
        return count
    
    def get_event_history(self, limit: Optional[int] = None) -> List[BaseEvent]:
        """获取事件历史记录"""
        if limit:
            return self._event_history[-limit:]
        return self._event_history.copy()
    
    def clear_history(self) -> None:
        """清空事件历史记录"""
        self._event_history.clear()


# 全局事件总线实例
event_bus = EventBus()


# 便捷装饰器
def event_handler(event_type: str, once: bool = False):
    """
    事件处理器装饰器
    
    Args:
        event_type: 要处理的事件类型
        once: 是否只处理一次
    """
    def decorator(func):
        if once:
            event_bus.subscribe_once(event_type, func)
        else:
            event_bus.subscribe(event_type, func)
        return func
    return decorator