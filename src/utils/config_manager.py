#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版配置管理器
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """配置管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.config = {}
        self.config_path = self._get_config_path()
        self.load_config()
    
    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        # 从当前文件位置找到项目根目录
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "config.json"
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}")
            # 创建默认配置
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._get_default_config(), f, indent=2, ensure_ascii=False)
            logger.info(f"已创建默认配置文件: {config_path}")
        
        return config_path
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "LOCAL_ASR": {
                "ENABLED": False,
                "PROVIDER": "aliyun",
                "ALIYUN_ASR": {
                    "access_key_id": "",
                    "access_key_secret": "",
                    "app_key": "",
                    "token": "",
                    "sample_rate": 16000,
                    "channels": 1,
                    "bits": 16,
                    "format": "wav"
                }
            }
        }
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"配置文件加载成功: {self.config_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.config = self._get_default_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项（支持点记法）
        
        Args:
            key: 配置键，支持点记法如 "LOCAL_ASR.ENABLED"
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config(self, key: str, value: Any):
        """
        设置配置项（支持点记法）
        
        Args:
            key: 配置键
            value: 配置值
        """
        try:
            keys = key.split('.')
            config = self.config
            
            # 导航到父节点
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            self.save_config()
        except Exception as e:
            logger.error(f"设置配置失败: {e}")
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance