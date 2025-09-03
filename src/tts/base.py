#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TTS抽象基类
定义文字转语音的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional


class TTSProviderBase(ABC):
    """TTS提供者基类"""
    
    @abstractmethod
    async def text_to_speak(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """
        文字转语音主函数
        
        Args:
            text: 要转换的文本
            output_file: 可选的输出文件路径，如果不提供则返回音频数据
            
        Returns:
            如果提供output_file，返回文件路径
            如果不提供output_file，返回音频数据bytes
            失败返回None
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