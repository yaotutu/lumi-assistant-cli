#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ASR抽象基类
定义语音识别的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional, List


class ASRProviderBase(ABC):
    """ASR提供者基类"""
    
    @abstractmethod
    async def recognize_speech(self, pcm_data: List[bytes], audio_format: str = "pcm") -> Optional[str]:
        """
        语音识别主函数
        
        Args:
            pcm_data: PCM音频数据列表
            audio_format: 音频格式，默认 "pcm"
            
        Returns:
            识别结果文本，失败返回None
        """
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """检查是否准备就绪"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """测试连接是否正常"""
        pass