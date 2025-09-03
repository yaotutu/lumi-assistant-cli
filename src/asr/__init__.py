#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ASR (Automatic Speech Recognition) 模块
只包含阿里云ASR功能
"""

# 导出阿里云ASR
from .aliyun_asr import AliyunASRClient

__all__ = ['AliyunASRClient']