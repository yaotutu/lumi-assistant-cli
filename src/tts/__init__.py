#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TTS (Text-to-Speech) 模块
只包含阿里云TTS功能
"""

# 导出阿里云TTS
from .aliyun_tts import AliyunTTSClient

__all__ = ['AliyunTTSClient']