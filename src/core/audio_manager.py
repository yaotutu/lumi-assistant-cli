#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音频管理器
负责音频录制、播放和处理
"""

import numpy as np
import sounddevice as sd
from collections import deque
from src.utils.logging.logging_config import get_logger
from .events.event_bus import event_bus, event_handler
from .events.event_types import (
    StartListeningEvent, StopListeningEvent, 
    AudioDataEvent, PlayAudioEvent
)

logger = get_logger(__name__)


class AudioManager:
    """音频管理器 - 处理音频录制和播放"""
    
    def __init__(self):
        # 音频参数
        self.sample_rate = 16000
        self.channels = 1
        self.frame_duration = 20  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        
        # 录音状态
        self.is_recording = False
        self.audio_buffer = deque()  # 存储录音数据
        
        # 音频流
        self.stream = None
        
        # 注册事件处理器
        self._register_event_handlers()
        
    def _register_event_handlers(self):
        """注册事件处理器"""
        event_bus.subscribe("audio.start_listening", self._handle_start_listening)
        event_bus.subscribe("audio.stop_listening", self._handle_stop_listening)
        event_bus.subscribe("audio.play", self._handle_play_audio)
        
    async def _handle_start_listening(self, event: StartListeningEvent):
        """处理开始录音事件"""
        if self.is_recording:
            logger.warning("已经在录音中...")
            return
            
        # 清空缓冲区
        self.audio_buffer.clear()
        self.is_recording = True
        
        print("\n🎤 开始录音...")
        print("📍 按 'e' 结束录音")
        
    async def _handle_stop_listening(self, event: StopListeningEvent):
        """处理停止录音事件"""
        if not self.is_recording:
            logger.warning("当前没有在录音")
            return
            
        self.is_recording = False
        
        # 获取所有录音数据
        if self.audio_buffer:
            # 合并所有音频块
            audio_data = np.concatenate(list(self.audio_buffer), axis=0)
            duration = len(audio_data) / self.sample_rate
            print(f"\n⏹️ 录音结束，时长: {duration:.1f} 秒")
            
            # 转换音频数据为PCM字节
            pcm_data = (audio_data[:, 0] * 32767).astype(np.int16).tobytes()
            
            # 发布音频数据事件
            audio_event = AudioDataEvent(
                source=event.source,
                audio_data=pcm_data,
                format="pcm",
                duration=duration
            )
            await event_bus.publish(audio_event)
        else:
            print("\n⚠️ 没有录到音频数据")
            
    async def _handle_play_audio(self, event: PlayAudioEvent):
        """处理播放音频事件"""
        try:
            if hasattr(self, 'audio_player') and self.audio_player:
                print("🔊 播放合成语音...")
                if event.format == "pcm":
                    self.audio_player.play_pcm(event.audio_data, blocking=True)
                else:
                    self.audio_player.play_wav(event.audio_data, blocking=True)
                print("✅ 语音播放完成")
            else:
                logger.warning("音频播放器未初始化")
        except Exception as e:
            logger.error(f"播放音频失败: {e}")
    
    def audio_callback(self, indata, _frames, _time_info, status):
        """音频输入回调"""
        if status:
            logger.warning(f"音频状态: {status}")
            
        if self.is_recording:
            # 存储音频数据
            self.audio_buffer.append(indata.copy())
            
    async def initialize(self):
        """初始化音频系统"""
        try:
            # 初始化音频播放器
            from src.utils.audio.audio_player import AudioPlayer
            self.audio_player = AudioPlayer(sample_rate=16000, channels=1)
            
            # 创建音频输入流
            self.stream = sd.InputStream(
                callback=self.audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.frame_size
            )
            
            # 启动音频流
            self.stream.start()
            logger.info("音频系统初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"音频系统初始化失败: {e}")
            return False
            
    async def cleanup(self):
        """清理音频资源"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            logger.info("音频资源已清理")


# 全局音频管理器实例
audio_manager = AudioManager()