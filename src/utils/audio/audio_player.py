#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音频播放器
用于播放PCM或WAV音频数据
"""

import io
import wave
import sounddevice as sd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioPlayer:
    """音频播放器"""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_playing = False
        
    def play_pcm(self, pcm_data: bytes, blocking: bool = True) -> bool:
        """
        播放PCM音频数据
        
        Args:
            pcm_data: PCM格式的音频数据
            blocking: 是否阻塞直到播放完成
            
        Returns:
            是否成功播放
        """
        try:
            if self.is_playing:
                logger.warning("音频正在播放中，请等待...")
                return False
                
            self.is_playing = True
            
            # 将PCM数据转换为numpy数组
            audio_array = np.frombuffer(pcm_data, dtype=np.int16)
            
            # 归一化到[-1, 1]范围
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 如果是单声道，确保shape正确
            if self.channels == 1:
                audio_float = audio_float.reshape(-1, 1)
                
            logger.debug(f"播放音频: 采样数={len(audio_float)}, 时长={len(audio_float)/self.sample_rate:.2f}秒")
            
            # 播放音频
            sd.play(audio_float, self.sample_rate, blocking=blocking)
            
            return True
            
        except Exception as e:
            logger.error(f"音频播放失败: {e}")
            return False
        finally:
            self.is_playing = False
    
    def play_wav(self, wav_data: bytes, blocking: bool = True) -> bool:
        """
        播放WAV音频数据
        
        Args:
            wav_data: WAV格式的音频数据
            blocking: 是否阻塞直到播放完成
            
        Returns:
            是否成功播放
        """
        try:
            if self.is_playing:
                logger.warning("音频正在播放中，请等待...")
                return False
                
            self.is_playing = True
            
            # 从内存中读取WAV数据
            wav_buffer = io.BytesIO(wav_data)
            with wave.open(wav_buffer, 'rb') as wav_file:
                # 获取音频参数
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                # 读取音频数据
                audio_data = wav_file.readframes(n_frames)
                
            # 转换为numpy数组
            if sample_width == 2:
                dtype = np.int16
            elif sample_width == 1:
                dtype = np.uint8
            else:
                raise ValueError(f"不支持的采样宽度: {sample_width}")
                
            audio_array = np.frombuffer(audio_data, dtype=dtype)
            
            # 归一化
            if dtype == np.int16:
                audio_float = audio_array.astype(np.float32) / 32768.0
            else:
                audio_float = (audio_array.astype(np.float32) - 128) / 128.0
            
            # 调整shape
            if channels == 1:
                audio_float = audio_float.reshape(-1, 1)
            else:
                audio_float = audio_float.reshape(-1, channels)
                
            logger.debug(f"播放WAV音频: 采样率={framerate}, 通道数={channels}, 时长={n_frames/framerate:.2f}秒")
            
            # 播放音频
            sd.play(audio_float, framerate, blocking=blocking)
            
            return True
            
        except Exception as e:
            logger.error(f"WAV音频播放失败: {e}")
            return False
        finally:
            self.is_playing = False
    
    def stop(self):
        """停止播放"""
        try:
            sd.stop()
            self.is_playing = False
            logger.debug("音频播放已停止")
        except Exception as e:
            logger.error(f"停止播放失败: {e}")
    
    def wait(self):
        """等待播放完成"""
        try:
            sd.wait()
            self.is_playing = False
        except Exception as e:
            logger.error(f"等待播放失败: {e}")