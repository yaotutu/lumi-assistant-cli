#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作控制器
提供统一的操作接口，支持任务管理和事件发布
"""
import asyncio
import time
import uuid
from typing import Dict, List, Optional
from asyncio import Queue
from src.utils.logging.logging_config import get_logger
from src.core.service_manager import service_manager
from src.core.audio_manager import audio_manager
from src.core.events.event_bus import event_bus, event_handler
from src.core.events.event_types import StartListeningEvent, StopListeningEvent, AudioDataEvent

logger = get_logger(__name__)


class OperationController:
    """
    统一的操作控制器 - 支持任务管理和事件发布
    """
    
    def __init__(self):
        self.current_recording_task: Optional[str] = None
        self.task_counter = 0
        self.event_subscribers: List[asyncio.Queue] = []
        self.active_tasks: Dict[str, dict] = {}
        self.pending_audio_tasks: Dict[str, asyncio.Queue] = {}
        self._setup_event_handlers()
    
    def generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        self.task_counter += 1
        return f"task_{self.task_counter}_{int(time.time())}"
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        event_bus.subscribe("audio.data", self._handle_audio_data)
    
    async def _handle_audio_data(self, event: AudioDataEvent):
        """处理音频数据事件"""
        # 如果有等待的任务，将音频数据发送给它
        if self.current_recording_task and self.current_recording_task in self.pending_audio_tasks:
            task_queue = self.pending_audio_tasks[self.current_recording_task]
            await task_queue.put(event.audio_data)
    
    async def start_recording(self) -> str:
        """开始录音 - 立即返回task_id"""
        if self.current_recording_task:
            raise Exception("Already recording")
        
        task_id = self.generate_task_id()
        self.current_recording_task = task_id
        
        # 记录任务
        self.active_tasks[task_id] = {
            "type": "voice_recording",
            "status": "recording",
            "created_at": time.time()
        }
        
        # 启动录音 - 通过事件系统
        from src.core.events.event_types import StartListeningEvent
        from src.core.events.event_bus import event_bus
        start_event = StartListeningEvent(source="grpc")
        await event_bus.publish(start_event)
        
        # 发布事件
        await self.publish_event({
            "task_id": task_id,
            "type": "RECORDING_STARTED",
            "content": "",
            "timestamp": int(time.time() * 1000)
        })
        
        return task_id
    
    async def stop_recording(self) -> str:
        """停止录音 - 立即返回task_id，启动后续处理"""
        if not self.current_recording_task:
            raise Exception("Not recording")
        
        task_id = self.current_recording_task
        
        # 创建音频数据等待队列
        audio_queue = Queue()
        self.pending_audio_tasks[task_id] = audio_queue
        
        # 更新任务状态
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "processing"
        
        # 停止录音 - 通过事件系统  
        stop_event = StopListeningEvent(source="grpc")
        await event_bus.publish(stop_event)
        
        # 发布停止事件
        await self.publish_event({
            "task_id": task_id,
            "type": "RECORDING_STOPPED", 
            "content": "",
            "timestamp": int(time.time() * 1000)
        })
        
        # 清除当前录音任务标记
        self.current_recording_task = None
        
        # 启动异步处理流程（等待音频数据）
        asyncio.create_task(self._process_voice_task_with_audio_wait(task_id, audio_queue))
        
        return task_id
    
    async def send_text(self, text: str) -> str:
        """发送文本 - 立即返回task_id，启动处理"""
        if not text.strip():
            raise Exception("Text cannot be empty")
        
        task_id = self.generate_task_id()
        
        # 记录任务
        self.active_tasks[task_id] = {
            "type": "text_processing",
            "status": "processing",
            "created_at": time.time()
        }
        
        # 启动异步处理
        asyncio.create_task(self._process_text_task(task_id, text.strip()))
        
        return task_id
    
    async def _process_voice_task_with_audio_wait(self, task_id: str, audio_queue: Queue):
        """等待音频数据并处理语音任务"""
        try:
            # 等待音频数据（设置超时避免无限等待）
            audio_data = await asyncio.wait_for(audio_queue.get(), timeout=10.0)
            
            # 清理等待队列
            if task_id in self.pending_audio_tasks:
                del self.pending_audio_tasks[task_id]
            
            # 调用标准的语音处理流程
            await self._process_voice_task(task_id, audio_data)
            
        except asyncio.TimeoutError:
            logger.error(f"Audio data timeout for task {task_id}")
            await self.publish_event({
                "task_id": task_id,
                "type": "TASK_ERROR",
                "content": "录音数据获取超时",
                "timestamp": int(time.time() * 1000)
            })
            # 清理资源
            self.active_tasks.pop(task_id, None)
            self.pending_audio_tasks.pop(task_id, None)
        except Exception as e:
            logger.error(f"Audio wait failed for task {task_id}: {e}")
            await self.publish_event({
                "task_id": task_id,
                "type": "TASK_ERROR", 
                "content": f"音频数据处理失败: {str(e)}",
                "timestamp": int(time.time() * 1000)
            })
            # 清理资源
            self.active_tasks.pop(task_id, None)
            self.pending_audio_tasks.pop(task_id, None)
    
    async def _process_voice_task(self, task_id: str, audio_data):
        """处理语音任务的完整流程"""
        try:
            # ASR处理
            if hasattr(service_manager, 'asr') and service_manager.asr:
                asr_result = await service_manager.asr.recognize(audio_data)
                await self.publish_event({
                    "task_id": task_id,
                    "type": "ASR_RESULT",
                    "content": asr_result,
                    "timestamp": int(time.time() * 1000)
                })
                
                # LLM处理
                await self._process_llm_task(task_id, asr_result)
            else:
                raise Exception("ASR service not available")
                
        except Exception as e:
            logger.error(f"Voice task {task_id} failed: {e}")
            await self.publish_event({
                "task_id": task_id,
                "type": "TASK_ERROR",
                "content": str(e),
                "timestamp": int(time.time() * 1000)
            })
        finally:
            # 清理任务
            self.active_tasks.pop(task_id, None)
    
    async def _process_text_task(self, task_id: str, text: str):
        """处理文本任务"""
        try:
            await self._process_llm_task(task_id, text)
        except Exception as e:
            logger.error(f"Text task {task_id} failed: {e}")
            await self.publish_event({
                "task_id": task_id,
                "type": "TASK_ERROR",
                "content": str(e),
                "timestamp": int(time.time() * 1000)
            })
        finally:
            # 清理任务
            self.active_tasks.pop(task_id, None)
    
    async def _process_llm_task(self, task_id: str, user_input: str):
        """LLM处理和TTS播放"""
        if not hasattr(service_manager, 'llm') or not service_manager.llm:
            raise Exception("LLM service not available")
        
        # LLM流式响应
        full_response = ""
        async for chunk in service_manager.llm.chat_stream(user_input):
            full_response += chunk
            await self.publish_event({
                "task_id": task_id,
                "type": "LLM_CHUNK",
                "content": chunk,
                "timestamp": int(time.time() * 1000)
            })
        
        # LLM完成
        await self.publish_event({
            "task_id": task_id,
            "type": "LLM_COMPLETE",
            "content": "",
            "timestamp": int(time.time() * 1000)
        })
        
        # TTS处理
        await self.publish_event({
            "task_id": task_id,
            "type": "TTS_STARTED",
            "content": "",
            "timestamp": int(time.time() * 1000)
        })
        
        if hasattr(service_manager, 'tts') and service_manager.tts:
            try:
                pcm_data = await service_manager.tts.text_to_speak(full_response)
                if pcm_data:
                    from src.utils.audio.audio_player import AudioPlayer
                    player = AudioPlayer()
                    await player.play_pcm(pcm_data, sample_rate=16000)
            except Exception as e:
                logger.warning(f"TTS playback failed: {e}")
        
        # TTS完成
        await self.publish_event({
            "task_id": task_id,
            "type": "TTS_COMPLETE",
            "content": "",
            "timestamp": int(time.time() * 1000)
        })
        
        # 任务完成
        await self.publish_event({
            "task_id": task_id,
            "type": "TASK_COMPLETE",
            "content": "",
            "timestamp": int(time.time() * 1000)
        })
    
    async def publish_event(self, event_data: dict):
        """发布事件给所有订阅者"""
        # 移除已断开的订阅者
        active_subscribers = []
        for subscriber in self.event_subscribers:
            try:
                await subscriber.put(event_data)
                active_subscribers.append(subscriber)
            except Exception as e:
                logger.debug(f"Removing disconnected subscriber: {e}")
        
        self.event_subscribers = active_subscribers
    
    def subscribe_events(self) -> asyncio.Queue:
        """订阅事件流"""
        event_queue = asyncio.Queue()
        self.event_subscribers.append(event_queue)
        return event_queue
    
    def unsubscribe_events(self, event_queue: asyncio.Queue):
        """取消事件订阅"""
        if event_queue in self.event_subscribers:
            self.event_subscribers.remove(event_queue)
    
    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "is_recording": self.current_recording_task is not None,
            "active_tasks": len(self.active_tasks),
            "active_clients": len(self.event_subscribers)
        }


# 全局操作控制器实例
operation_controller = OperationController()