# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

py-xiaozhi 是一个极简AI语音助手，专为CLI环境设计。实现了完整的语音交互流程：语音识别(ASR) → 大语言模型处理(LLM) → 语音合成(TTS) → 音频播放。主要基于阿里云语音服务和OpenAI兼容的LLM API。

## 常用开发命令

### 运行应用
```bash
# 运行主程序
python main.py

# 测试LLM配置和连接
python test_llm.py
```

### 环境配置
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# 安装依赖
pip install -r requirements.txt

# macOS特定依赖（用于Opus音频编解码）
brew install opus
```

### 测试和调试
```bash
# 没有专门的测试框架，使用独立测试脚本：
python test_llm.py  # 测试LLM功能
```

## 核心架构

### 应用流程
1. **main.py** - 入口程序，管理用户交互循环
2. **音频录制** - 使用sounddevice捕获麦克风输入  
3. **ASR识别** - 调用阿里云ASR服务识别语音为文本
4. **LLM处理** - 将识别文本发送给LLM获取智能回复
5. **TTS合成** - 将LLM回复通过阿里云TTS转为语音
6. **音频播放** - 播放合成的语音

### 模块架构
```
src/
├── asr/           # 语音识别模块
│   ├── base.py    # ASR基类定义
│   └── aliyun_asr.py  # 阿里云ASR实现
├── llm/           # 大语言模型集成
│   ├── base.py    # LLM提供者基类
│   ├── openai_llm.py  # OpenAI兼容API实现
│   └── __init__.py
├── tts/           # 语音合成模块
│   ├── base.py    # TTS基类定义
│   └── aliyun_tts.py  # 阿里云TTS实现
└── utils/         # 工具模块
    ├── config_manager.py  # 配置管理
    ├── audio_player.py   # 音频播放
    └── logging_config.py # 日志配置
```

### 异步架构特点
- 主程序使用异步I/O处理音频和网络请求
- ASR、LLM、TTS都实现为异步客户端
- 音频处理使用sounddevice的非阻塞回调模式
- 配置管理采用单例模式，支持点记法访问

## 关键配置

### 配置文件结构 (config/config.json)
```json
{
  "LOCAL_ASR": {
    "ENABLED": true,
    "PROVIDER": "aliyun",  // 目前只支持阿里云
    "ALIYUN_ASR": {
      "access_key_id": "",
      "access_key_secret": "", 
      "token": "...",        // NLS服务token
      "app_key": "...",      // 应用密钥
      "sample_rate": 16000
    }
  },
  "LOCAL_TTS": {
    "ENABLED": true,
    "PROVIDER": "aliyun",
    "ALIYUN_TTS": {
      "voice": "zhixiaobai", // 声音类型
      "volume": 50,
      "speech_rate": 0,
      "pitch_rate": 0
    }
  },
  "LLM": {
    "ENABLED": true,
    "PROVIDER": "openai",   // 支持OpenAI兼容API
    "OPENAI_LLM": {
      "api_key": "sk-...",
      "base_url": "https://api.siliconflow.cn/v1",  // 可自定义
      "model": "Qwen/Qwen3-30B-A3B",
      "max_tokens": 2000,
      "temperature": 0.7
    }
  }
}
```

### LLM服务配置要点
- 支持所有OpenAI兼容的API服务（SiliconFlow、DeepSeek、通义千问等）
- `base_url` 可指向本地部署的LLM服务
- 超时时间设为60秒以适应大模型响应
- 自动处理SOCKS代理环境变量冲突

## 开发注意事项

### 音频处理
- 固定使用16kHz采样率，单声道
- 音频数据以numpy数组形式传递
- 需要libopus库支持音频编解码（macOS通过Homebrew安装）

### 异步编程模式
- 所有网络请求必须使用async/await
- 音频回调函数运行在独立线程，需要线程安全的数据结构
- 配置管理器是全局单例，可安全跨模块访问

### 错误处理策略
- LLM连接失败不阻断程序运行，自动降级为直接TTS播放ASR结果
- ASR失败会重试，TTS失败会打印警告但不中断流程
- 网络服务都有超时保护机制

### 扩展新的服务提供商
1. **ASR/TTS**: 继承对应的基类(`ASRBase`/`TTSBase`)，实现异步接口
2. **LLM**: 继承`LLMProviderBase`，实现`chat`和`chat_with_tools`方法
3. 在配置文件中添加新的provider配置段
4. 在初始化代码中添加对新provider的支持

### 依赖库关键点
- `sounddevice`: 跨平台音频I/O，需要系统音频权限
- `numpy`: 音频数据数值计算
- `aiohttp/websockets`: 与阿里云服务异步通信  
- `openai`: LLM API客户端，支持异步操作
- `colorlog`: 彩色日志输出增强调试体验