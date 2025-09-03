#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阿里云TTS客户端
基于阿里云智能语音交互 NLS-Gateway API
支持文字转语音功能
"""

import json
import uuid
import asyncio
import logging
import hmac
import hashlib
import base64
import requests
import time
from urllib import parse
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from src.tts.base import TTSProviderBase

logger = logging.getLogger(__name__)


class AccessToken:
    """阿里云Access Token生成器"""
    @staticmethod
    def _encode_text(text):
        encoded_text = parse.quote_plus(text)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def _encode_dict(dic):
        keys = dic.keys()
        dic_sorted = [(key, dic[key]) for key in sorted(keys)]
        encoded_text = parse.urlencode(dic_sorted)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def create_token(access_key_id, access_key_secret):
        parameters = {
            "AccessKeyId": access_key_id,
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": "cn-shanghai",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid1()),
            "SignatureVersion": "1.0",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "Version": "2019-02-28",
        }
        # 构造规范化的请求字符串
        query_string = AccessToken._encode_dict(parameters)
        # 构造待签名字符串
        string_to_sign = (
            "GET"
            + "&"
            + AccessToken._encode_text("/")
            + "&"
            + AccessToken._encode_text(query_string)
        )
        # 计算签名
        secreted_string = hmac.new(
            bytes(access_key_secret + "&", encoding="utf-8"),
            bytes(string_to_sign, encoding="utf-8"),
            hashlib.sha1,
        ).digest()
        signature = base64.b64encode(secreted_string)
        # 进行URL编码
        signature = AccessToken._encode_text(signature)
        # 调用服务
        full_url = "http://nls-meta.cn-shanghai.aliyuncs.com/?Signature=%s&%s" % (
            signature,
            query_string,
        )
        # 提交HTTP GET请求
        response = requests.get(full_url)
        if response.ok:
            root_obj = response.json()
            key = "Token"
            if key in root_obj:
                token = root_obj[key]["Id"]
                expire_time = root_obj[key]["ExpireTime"]
                return token, expire_time
        return None, None


@dataclass
class AliyunTTSConfig:
    """阿里云TTS配置参数"""
    # 认证方式1：使用密钥对（推荐）
    access_key_id: Optional[str] = None
    access_key_secret: Optional[str] = None
    # 认证方式2：直接使用Token
    token: Optional[str] = None
    # 应用配置
    app_key: str = ""
    # 音频参数
    sample_rate: int = 16000
    format: str = "pcm"  # pcm或wav
    # 声音配置
    voice: str = "xiaoyun"  # 发音人
    volume: int = 50  # 音量，取值范围0~100
    speech_rate: int = 0  # 语速，取值范围-500~500
    pitch_rate: int = 0  # 语调，取值范围-500~500


class AliyunTTSClient(TTSProviderBase):
    """阿里云TTS文字转语音客户端"""
    
    def __init__(self, config: AliyunTTSConfig):
        self.config = config
        
        # API配置
        self.host = "nls-gateway-cn-shanghai.aliyuncs.com"
        self.api_url = f"https://{self.host}/stream/v1/tts"
        self.header = {"Content-Type": "application/json"}
        
        # 状态管理
        self.is_processing = False
        
        # Token管理
        if self.config.access_key_id and self.config.access_key_secret:
            # 使用密钥对生成临时token
            self._refresh_token()
        else:
            # 直接使用预生成的长期token
            self.token = self.config.token
            self.expire_time = None
    
    def _refresh_token(self):
        """刷新Token并记录过期时间"""
        if self.config.access_key_id and self.config.access_key_secret:
            self.token, expire_time_str = AccessToken.create_token(
                self.config.access_key_id, self.config.access_key_secret
            )
            if not expire_time_str:
                raise ValueError("无法获取有效的Token过期时间")

            try:
                # 统一转换为字符串处理
                expire_str = str(expire_time_str).strip()

                if expire_str.isdigit():
                    expire_time = datetime.fromtimestamp(int(expire_str))
                else:
                    expire_time = datetime.strptime(expire_str, "%Y-%m-%dT%H:%M:%SZ")
                self.expire_time = expire_time.timestamp() - 60  # 提前60秒过期
            except Exception as e:
                raise ValueError(f"无效的过期时间格式: {expire_str}") from e

        else:
            self.expire_time = None

        if not self.token:
            raise ValueError("无法获取有效的访问Token")

    def _is_token_expired(self):
        """检查Token是否过期"""
        if not self.expire_time:
            return False  # 长期Token不过期
        return time.time() > self.expire_time

    async def text_to_speak(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """
        文字转语音主函数
        
        Args:
            text: 要转换的文本
            output_file: 可选的输出文件路径
            
        Returns:
            如果提供output_file，返回文件路径
            如果不提供output_file，返回音频数据bytes
            失败返回None
        """
        if self.is_processing:
            logger.warning("正在处理其他TTS任务，请稍后再试")
            return None
        
        # 检查并刷新Token
        if self._is_token_expired():
            logger.warning("Token已过期，正在自动刷新...")
            self._refresh_token()
        
        try:
            self.is_processing = True
            
            request_json = {
                "appkey": self.config.app_key,
                "token": self.token,
                "text": text,
                "format": self.config.format,
                "sample_rate": self.config.sample_rate,
                "voice": self.config.voice,
                "volume": self.config.volume,
                "speech_rate": self.config.speech_rate,
                "pitch_rate": self.config.pitch_rate,
            }

            logger.debug(f"开始TTS转换: {text[:50]}...")
            
            # 使用asyncio运行同步请求
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None, 
                lambda: requests.post(
                    self.api_url, 
                    json.dumps(request_json), 
                    headers=self.header
                )
            )
            
            # 检查返回请求数据的mime类型是否是audio/***
            if resp.headers.get("Content-Type", "").startswith("audio/"):
                audio_data = resp.content
                logger.debug(f"TTS转换成功，音频大小: {len(audio_data)} 字节")
                
                if output_file:
                    # 保存到文件
                    with open(output_file, "wb") as f:
                        f.write(audio_data)
                    return output_file.encode()  # 返回文件路径的bytes
                else:
                    # 返回音频数据
                    return audio_data
            else:
                # 解析错误信息
                try:
                    error_data = json.loads(resp.content)
                    status_code = error_data.get("status")
                    logger.error(f"TTS失败，状态码: {status_code}, 响应: {resp.content}")
                except:
                    logger.error(f"TTS失败，HTTP状态: {resp.status_code}, 响应: {resp.content}")
                return None
                
        except Exception as e:
            logger.error(f"TTS转换失败: {e}")
            return None
        finally:
            self.is_processing = False
    
    def is_ready(self) -> bool:
        """检查是否准备就绪"""
        return not self.is_processing
    
    async def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            # 测试TTS一个简单的文本
            result = await self.text_to_speak("测试", None)
            
            # 如果返回音频数据，说明连接正常
            return result is not None and len(result) > 0
            
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False