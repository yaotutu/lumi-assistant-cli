#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
极简语音助手
按 b 开始录音
按 e 结束录音并识别，然后进行TTS播放
按 q 退出程序
"""

import asyncio
import sys
import numpy as np
import sounddevice as sd
from collections import deque

from src.utils.config_manager import ConfigManager
from src.utils.logging_config import setup_logging, get_logger
from src.llm import OpenAILLM

logger = get_logger(__name__)


class VoiceRecorder:
    """语音录制器"""
    
    def __init__(self):
        setup_logging()
        self.config = ConfigManager.get_instance()
        
        # 音频参数
        self.sample_rate = 16000
        self.channels = 1
        self.frame_duration = 20  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        
        # 录音状态
        self.is_recording = False
        self.audio_buffer = deque()  # 存储录音数据
        
        # ASR客户端
        self.asr_client = None
        # LLM客户端
        self.llm_client = None
        # TTS客户端
        self.tts_client = None
        # 音频播放器
        self.audio_player = None
        
        # 音频流
        self.stream = None
        
    def audio_callback(self, indata, frames, time_info, status):
        """音频输入回调"""
        if status:
            print(f"⚠️ 音频状态: {status}")
            
        if self.is_recording:
            # 存储音频数据
            self.audio_buffer.append(indata.copy())
            
    async def init_asr(self):
        """初始化ASR"""
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
                
                self.asr_client = AliyunASRClient(asr_config, self.on_asr_result)
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
        """初始化LLM"""
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
                    self.llm_client = None  # 清空LLM客户端
                    return False
            else:
                print(f"❌ 不支持的LLM提供商: {provider}")
                return False
                
        except Exception as e:
            print(f"❌ LLM初始化失败: {e}")
            print("💡 将跳过LLM功能，程序仍可正常使用ASR和TTS")
            logger.error(f"LLM初始化错误: {e}", exc_info=True)
            self.llm_client = None  # 确保LLM客户端为空
            return False
    
    async def init_tts(self):
        """初始化TTS"""
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
                
                # 初始化音频播放器
                from src.utils.audio_player import AudioPlayer
                self.audio_player = AudioPlayer(sample_rate=16000, channels=1)
                
                print("✅ TTS初始化成功")
                return True
            else:
                print(f"❌ 不支持的TTS提供商: {provider}")
                return False
                
        except Exception as e:
            print(f"⚠️ TTS初始化失败: {e}，TTS功能将不可用")
            logger.error(f"TTS初始化错误: {e}", exc_info=True)
            return False
            
    def on_asr_result(self, result):
        """ASR识别结果回调"""
        if result:
            print(f"\n📝 识别结果: {result}")
            print("-" * 50)
        
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            print("⚠️ 已经在录音中...")
            return
            
        # 清空缓冲区
        self.audio_buffer.clear()
        self.is_recording = True
        
        print("\n🎤 开始录音...")
        print("📍 按 'e' 结束录音")
        
    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            print("⚠️ 当前没有在录音")
            return None
            
        self.is_recording = False
        
        # 获取所有录音数据
        if self.audio_buffer:
            # 合并所有音频块
            audio_data = np.concatenate(list(self.audio_buffer), axis=0)
            duration = len(audio_data) / self.sample_rate
            print(f"\n⏹️ 录音结束，时长: {duration:.1f} 秒")
            return audio_data
        else:
            print("\n⚠️ 没有录到音频数据")
            return None
            
    async def process_audio(self, audio_data):
        """处理录音数据，发送到ASR，然后进行TTS"""
        if audio_data is None or len(audio_data) == 0:
            return
            
        print("📤 发送音频到ASR进行识别...")
        
        try:
            # 转换音频数据为PCM字节
            pcm_data = (audio_data[:, 0] * 32767).astype(np.int16).tobytes()
            
            # 发送到ASR进行识别
            result = await self.asr_client.recognize_speech([pcm_data], "pcm")
            
            if result:
                print(f"\n📝 识别结果: {result}")
                print("-" * 50)
                
                # 如果LLM可用，先调用LLM处理用户输入
                llm_response = None
                if self.llm_client:
                    print("🤖 正在调用LLM处理...")
                    try:
                        llm_response = await self.llm_client.chat(result)
                        if llm_response:
                            print(f"\n🤖 LLM回复: {llm_response}")
                            print("-" * 50)
                        else:
                            print("⚠️ LLM未返回回复")
                            llm_response = "抱歉，我没有理解您的意思。"
                    except Exception as e:
                        print(f"⚠️ LLM调用失败: {e}")
                        llm_response = "抱歉，我现在有些问题，请稍后再试。"
                else:
                    # 如果LLM不可用，直接使用ASR结果
                    llm_response = result
                
                # 如果TTS可用，对LLM回复进行TTS转换并播放
                if self.tts_client and self.audio_player and llm_response:
                    print("\n⏳ 等待1秒后进行语音合成...")
                    await asyncio.sleep(1)
                    
                    print("🎤 正在进行语音合成...")
                    tts_audio = await self.tts_client.text_to_speak(llm_response)
                    
                    if tts_audio:
                        print("🔊 播放合成语音...")
                        # 根据TTS格式选择播放方式
                        if self.config.get_config("LOCAL_TTS.ALIYUN_TTS.format", "pcm") == "pcm":
                            self.audio_player.play_pcm(tts_audio, blocking=True)
                        else:
                            self.audio_player.play_wav(tts_audio, blocking=True)
                        print("✅ 语音播放完成")
                    else:
                        print("⚠️ 语音合成失败")
                elif llm_response:
                    print("⚠️ TTS不可用，无法播放语音")
            else:
                print("\n⚠️ 未识别到内容")
                
        except Exception as e:
            print(f"\n❌ 处理音频失败: {e}")
            logger.error(f"音频处理错误: {e}", exc_info=True)
            
    async def close(self):
        """关闭资源"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            

async def main():
    """主函数"""
    print("=" * 60)
    print("🎙️  语音识别程序")
    print("=" * 60)
    print("操作说明:")
    print("  b - 开始录音")
    print("  e - 结束录音并识别")
    print("  q - 退出程序")
    print("=" * 60)
    
    recorder = VoiceRecorder()
    
    # 初始化ASR
    if not await recorder.init_asr():
        print("❌ 程序初始化失败")
        return
    
    # 初始化LLM（可选）
    llm_available = await recorder.init_llm()
    
    # 初始化TTS（可选）
    tts_available = await recorder.init_tts()
    
    # 显示可用组件状态
    print("\n📊 系统组件状态：")
    print(f"  🎯 ASR: ✅ 可用")
    print(f"  🤖 LLM: {'✅ 可用' if llm_available else '❌ 不可用'}")
    print(f"  🎤 TTS: {'✅ 可用' if tts_available else '❌ 不可用'}")
    print()
        
    # 创建音频输入流
    recorder.stream = sd.InputStream(
        callback=recorder.audio_callback,
        channels=recorder.channels,
        samplerate=recorder.sample_rate,
        blocksize=recorder.frame_size
    )
    
    try:
        # 启动音频流
        recorder.stream.start()
        print("\n✅ 系统就绪！")
        print("📍 按 'b' 开始录音\n")
        
        # 主循环
        while True:
            # 获取用户输入
            cmd = input().strip().lower()
            
            if cmd == 'b':
                # 开始录音
                recorder.start_recording()
                
            elif cmd == 'e':
                # 结束录音并识别
                audio_data = recorder.stop_recording()
                if audio_data is not None:
                    await recorder.process_audio(audio_data)
                print("\n📍 按 'b' 开始新的录音")
                
            elif cmd == 'q':
                print("\n👋 退出程序...")
                break
                
            elif cmd == '':
                continue  # 忽略空输入
                
            else:
                print(f"❓ 未知命令: {cmd}")
                print("   使用 b:开始 / e:结束 / q:退出")
                
            # 给异步任务一点时间
            await asyncio.sleep(0.1)
                    
    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被中断")
        
    finally:
        await recorder.close()
        print("✅ 程序已退出")
        

if __name__ == "__main__":
    # 运行程序
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        logger.error(f"主程序错误: {e}", exc_info=True)