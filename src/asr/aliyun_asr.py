#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阿里云ASR客户端
基于阿里云智能语音交互 NLS-Gateway API
支持非流式语音识别功能
"""

import json
import uuid
import asyncio
import http.client
import logging
import hmac
import hashlib
import base64
import requests
import time
from urllib import parse
from datetime import datetime
from typing import Optional, List, Callable
from dataclasses import dataclass
from src.asr.base import ASRProviderBase

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
class AliyunASRConfig:
    """阿里云ASR配置参数"""
    # 认证方式1：使用密钥对（推荐）
    access_key_id: Optional[str] = None
    access_key_secret: Optional[str] = None
    # 认证方式2：直接使用Token
    token: Optional[str] = None
    # 应用配置
    app_key: str = ""
    # 音频参数
    sample_rate: int = 16000
    channels: int = 1
    bits: int = 16
    format: str = "wav"
    

class AliyunASRClient(ASRProviderBase):
    """阿里云ASR非流式语音识别客户端"""
    
    def __init__(self, config: AliyunASRConfig, on_result_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.on_result_callback = on_result_callback
        
        # API配置
        self.host = "nls-gateway-cn-shanghai.aliyuncs.com"
        self.base_url = f"https://{self.host}/stream/v1/asr"
        
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

    def _construct_request_url(self) -> str:
        """构造请求URL，包含参数"""
        request = f"{self.base_url}?appkey={self.config.app_key}"
        request += f"&format={self.config.format}"
        request += f"&sample_rate={self.config.sample_rate}"
        request += "&enable_punctuation_prediction=true"
        request += "&enable_inverse_text_normalization=true"
        request += "&enable_voice_detection=false"
        return request
    
    async def _send_request(self, pcm_data: bytes) -> Optional[str]:
        """发送请求到阿里云ASR服务"""
        try:
            # 设置HTTP头
            headers = {
                "X-NLS-Token": self.token,
                "Content-type": "application/octet-stream",
                "Content-Length": str(len(pcm_data)),
            }

            # 创建连接并发送请求
            conn = http.client.HTTPSConnection(self.host)
            request_url = self._construct_request_url()

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.request(
                    method="POST", url=request_url, body=pcm_data, headers=headers
                ),
            )

            # 获取响应
            response = await loop.run_in_executor(None, conn.getresponse)
            body = await loop.run_in_executor(None, response.read)
            conn.close()

            # 解析响应
            try:
                body_json = json.loads(body)
                status = body_json.get("status")

                if status == 20000000:
                    result = body_json.get("result", "")
                    logger.debug(f"ASR结果: {result}")
                    return result
                else:
                    logger.error(f"ASR失败，状态码: {status}")
                    return None

            except ValueError:
                logger.error("响应不是JSON格式")
                return None

        except Exception as e:
            logger.error(f"ASR请求失败: {e}")
            return None
    
    async def recognize_speech(self, pcm_data: List[bytes], audio_format: str = "pcm") -> Optional[str]:
        """
        语音识别主函数
        
        Args:
            pcm_data: PCM音频数据列表
            audio_format: 音频格式，默认 "pcm"
            
        Returns:
            识别结果文本，失败返回None
        """
        if self.is_processing:
            logger.warning("正在处理其他识别任务，请稍后再试")
            return None
        
        # 检查并刷新Token
        if self._is_token_expired():
            logger.warning("Token已过期，正在自动刷新...")
            self._refresh_token()
        
        try:
            self.is_processing = True
            
            # 处理PCM音频数据
            combined_pcm_data = b"".join(pcm_data)
            
            if not combined_pcm_data:
                logger.warning("音频数据为空")
                return ""
            
            logger.debug(f"开始语音识别，音频长度: {len(combined_pcm_data)} 字节")
            
            # 发送请求并获取文本
            result = await self._send_request(combined_pcm_data)
            
            # 执行回调
            if result and self.on_result_callback:
                try:
                    self.on_result_callback(result)
                except Exception as e:
                    logger.error(f"回调函数执行失败: {str(e)}")
            
            return result if result else ""
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return None
        finally:
            self.is_processing = False
    
    def is_ready(self) -> bool:
        """检查是否准备就绪"""
        return not self.is_processing
    
    async def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            # 创建测试音频数据（1秒静音）
            import struct
            
            sample_count = self.config.sample_rate * 1  # 1秒
            test_pcm = struct.pack('<' + 'h' * sample_count, *([0] * sample_count))
            
            # 尝试识别测试音频
            result = await self.recognize_speech([test_pcm], "pcm")
            
            # 如果返回空字符串或识别结果，说明连接正常
            return result is not None
            
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False