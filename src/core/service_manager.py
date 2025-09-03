#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务管理器
负责初始化和管理ASR、LLM、TTS等服务
"""

from src.utils.config.config_manager import ConfigManager
from src.utils.logging.logging_config import get_logger
from src.llm import OpenAILLM
from .events.event_bus import event_bus
from .events.event_types import (
    AudioDataEvent, ASRResultEvent, LLMResponseEvent,
    PlayAudioEvent
)

logger = get_logger(__name__)


class ServiceManager:
    """服务管理器 - 管理ASR、LLM、TTS等服务"""
    
    def __init__(self):
        self.config = ConfigManager.get_instance()
        
        # 服务客户端
        self.asr_client = None
        self.llm_client = None
        self.tts_client = None
        
        # 注册事件处理器
        self._register_event_handlers()
        
    def _register_event_handlers(self):
        """注册事件处理器"""
        event_bus.subscribe("audio.data", self._handle_audio_data)
        event_bus.subscribe("text.asr_result", self._handle_asr_result)
        event_bus.subscribe("text.llm_response", self._handle_llm_response)
        
    async def _handle_audio_data(self, event: AudioDataEvent):
        """处理音频数据 - 发送到ASR"""
        if not self.asr_client:
            logger.warning("ASR服务未初始化")
            return
            
        try:
            print("📤 发送音频到ASR进行识别...")
            
            # 发送到ASR进行识别
            result = await self.asr_client.recognize_speech([event.audio_data], event.format)
            
            if result:
                print(f"\n📝 识别结果: {result}")
                print("-" * 50)
                
                # 发布ASR结果事件
                asr_event = ASRResultEvent(
                    source=event.source,
                    text=result,
                    confidence=1.0
                )
                await event_bus.publish(asr_event)
            else:
                print("\n⚠️ 未识别到内容")
                
        except Exception as e:
            logger.error(f"ASR处理失败: {e}")
            
    async def _handle_asr_result(self, event: ASRResultEvent):
        """处理ASR结果 - 发送到LLM"""
        if not self.llm_client:
            # 如果LLM不可用，直接进行TTS
            await self._perform_tts(event.text, event.source)
            return
            
        try:
            print("🤖 正在调用LLM处理...")
            
            response = await self.llm_client.chat(event.text)
            
            if response:
                print(f"\n🤖 LLM回复: {response}")
                print("-" * 50)
                
                # 发布LLM回复事件
                llm_event = LLMResponseEvent(
                    source=event.source,
                    text=response,
                    model=self.config.get_config("LLM.OPENAI_LLM.model", "")
                )
                await event_bus.publish(llm_event)
            else:
                print("⚠️ LLM未返回回复")
                await self._perform_tts("抱歉，我没有理解您的意思。", event.source)
                
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            await self._perform_tts("抱歉，我现在有些问题，请稍后再试。", event.source)
            
    async def _handle_llm_response(self, event: LLMResponseEvent):
        """处理LLM回复 - 进行TTS"""
        await self._perform_tts(event.text, event.source)
        
    async def _perform_tts(self, text: str, source: str):
        """执行TTS转换并播放"""
        if not self.tts_client:
            logger.warning("TTS服务未初始化，无法播放语音")
            return
            
        try:
            print("\n⏳ 等待1秒后进行语音合成...")
            import asyncio
            await asyncio.sleep(1)
            
            print("🎤 正在进行语音合成...")
            tts_audio = await self.tts_client.text_to_speak(text)
            
            if tts_audio:
                # 发布播放音频事件
                format_type = self.config.get_config("LOCAL_TTS.ALIYUN_TTS.format", "pcm")
                play_event = PlayAudioEvent(
                    source=source,
                    audio_data=tts_audio,
                    format=format_type,
                    blocking=True
                )
                await event_bus.publish(play_event)
            else:
                print("⚠️ 语音合成失败")
                
        except Exception as e:
            logger.error(f"TTS处理失败: {e}")
    
    async def init_asr(self):
        """初始化ASR服务"""
        try:
            # 检查配置
            if not self.config.get_config("LOCAL_ASR.ENABLED", False):
                print("❌ 本地ASR未启用，请检查 config/config.json")
                return False
                
            provider = self.config.get_config("LOCAL_ASR.PROVIDER", "aliyun")
            
            if provider == "aliyun":
                print("🔧 初始化阿里云ASR...")
                from src.asr.aliyun_asr import AliyunASRClient, AliyunASRConfig
                
                # 从配置文件创建ASR配置
                asr_config = AliyunASRConfig(
                    access_key_id=self.config.get_config("LOCAL_ASR.ALIYUN_ASR.access_key_id", ""),
                    access_key_secret=self.config.get_config("LOCAL_ASR.ALIYUN_ASR.access_key_secret", ""),
                    app_key=self.config.get_config("LOCAL_ASR.ALIYUN_ASR.app_key", ""),
                    token=self.config.get_config("LOCAL_ASR.ALIYUN_ASR.token", ""),
                    sample_rate=self.config.get_config("LOCAL_ASR.ALIYUN_ASR.sample_rate", 16000),
                    format=self.config.get_config("LOCAL_ASR.ALIYUN_ASR.format", "wav")
                )
                
                self.asr_client = AliyunASRClient(asr_config, self._on_asr_result)
                print("✅ ASR初始化成功")
                return True
            else:
                print(f"❌ 不支持的ASR提供商: {provider}")
                return False
                
        except Exception as e:
            print(f"❌ ASR初始化失败: {e}")
            logger.error(f"ASR初始化错误: {e}", exc_info=True)
            return False
    
    async def init_llm(self):
        """初始化LLM服务"""
        try:
            # 检查配置
            if not self.config.get_config("LLM.ENABLED", False):
                print("❌ LLM未启用，请检查 config/config.json")
                return False
                
            provider = self.config.get_config("LLM.PROVIDER", "openai")
            
            if provider == "openai":
                print("🔧 初始化OpenAI LLM...")
                
                # 从配置文件创建LLM配置
                llm_config = {
                    "api_key": self.config.get_config("LLM.OPENAI_LLM.api_key", ""),
                    "base_url": self.config.get_config("LLM.OPENAI_LLM.base_url", "https://api.openai.com/v1"),
                    "model": self.config.get_config("LLM.OPENAI_LLM.model", "gpt-3.5-turbo"),
                    "max_tokens": self.config.get_config("LLM.OPENAI_LLM.max_tokens", 2000),
                    "temperature": self.config.get_config("LLM.OPENAI_LLM.temperature", 0.7)
                }
                
                self.llm_client = OpenAILLM(llm_config)
                
                # 测试连接
                if await self.llm_client.test_connection():
                    print("✅ LLM初始化成功")
                    return True
                else:
                    print("⚠️ LLM连接测试失败，将跳过LLM功能")
                    print("💡 要启用LLM功能，请在config/config.json中配置正确的API密钥")
                    self.llm_client = None
                    return False
            else:
                print(f"❌ 不支持的LLM提供商: {provider}")
                return False
                
        except Exception as e:
            print(f"❌ LLM初始化失败: {e}")
            print("💡 将跳过LLM功能，程序仍可正常使用ASR和TTS")
            logger.error(f"LLM初始化错误: {e}", exc_info=True)
            self.llm_client = None
            return False
            
    async def init_tts(self):
        """初始化TTS服务"""
        try:
            # 检查配置
            if not self.config.get_config("LOCAL_TTS.ENABLED", False):
                print("❌ 本地TTS未启用，跳过TTS功能")
                return False
                
            provider = self.config.get_config("LOCAL_TTS.PROVIDER", "aliyun")
            
            if provider == "aliyun":
                print("🔧 初始化阿里云TTS...")
                from src.tts.aliyun_tts import AliyunTTSClient, AliyunTTSConfig
                
                # 从配置文件创建TTS配置
                tts_config = AliyunTTSConfig(
                    access_key_id=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.access_key_id", ""),
                    access_key_secret=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.access_key_secret", ""),
                    app_key=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.app_key", ""),
                    token=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.token", ""),
                    sample_rate=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.sample_rate", 16000),
                    format=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.format", "pcm"),
                    voice=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.voice", "xiaoyun"),
                    volume=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.volume", 50),
                    speech_rate=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.speech_rate", 0),
                    pitch_rate=self.config.get_config("LOCAL_TTS.ALIYUN_TTS.pitch_rate", 0)
                )
                
                self.tts_client = AliyunTTSClient(tts_config)
                
                print("✅ TTS初始化成功")
                return True
            else:
                print(f"❌ 不支持的TTS提供商: {provider}")
                return False
                
        except Exception as e:
            print(f"⚠️ TTS初始化失败: {e}，TTS功能将不可用")
            logger.error(f"TTS初始化错误: {e}", exc_info=True)
            return False
            
    def _on_asr_result(self, result):
        """ASR识别结果回调（兼容性）"""
        # 这个回调可能被ASR客户端使用，但在事件系统中我们不再需要它
        pass
        
    async def initialize_all(self):
        """初始化所有服务"""
        print("🚀 初始化服务...")
        
        # 初始化ASR
        asr_success = await self.init_asr()
        if not asr_success:
            return False
        
        # 初始化LLM（可选）
        llm_success = await self.init_llm()
        
        # 初始化TTS（可选）
        tts_success = await self.init_tts()
        
        # 显示可用组件状态
        print("\n📊 系统组件状态：")
        print(f"  🎯 ASR: {'✅ 可用' if asr_success else '❌ 不可用'}")
        print(f"  🤖 LLM: {'✅ 可用' if llm_success else '❌ 不可用'}")
        print(f"  🎤 TTS: {'✅ 可用' if tts_success else '❌ 不可用'}")
        print()
        
        return asr_success  # ASR是必需的，其他是可选的


# 全局服务管理器实例
service_manager = ServiceManager()