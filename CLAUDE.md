# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

lumi-assistant 是一个现代化的AI语音助手平台，采用事件驱动架构和模块化设计。实现了完整的语音交互流程：语音识别(ASR) → 大语言模型处理(LLM) → 语音合成(TTS) → 音频播放。支持多种界面（CLI、gRPC、未来扩展GUI），集成对话管理、会话存储等企业级功能。

## 常用开发命令

### 运行应用
```bash
# 运行主程序（使用系统Python）
python main.py

# 或使用uv运行（推荐）
uv run python main.py

# 测试LLM配置和连接
python tests/unit/test_llm.py
```

### 环境配置
```bash
# 使用uv管理依赖（推荐）
uv sync

# 传统方式
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 测试和调试
```bash
# 运行单元测试
python tests/unit/test_llm.py

# 查看应用日志
tail -f src/logs/app.log

# 测试gRPC（如果需要）
python scripts/test_grpc.py
```

## 核心架构

### 应用流程
1. **main.py** - 入口程序，管理用户交互循环
2. **音频录制** - 使用sounddevice捕获麦克风输入，转换为PCM格式  
3. **ASR识别** - 将PCM音频数据发送到阿里云ASR服务识别为文本
4. **LLM处理** - 将识别文本发送给LLM获取智能回复
5. **TTS合成** - 将LLM回复通过阿里云TTS转为PCM音频数据
6. **音频播放** - 直接播放PCM格式的合成语音

### 模块架构
```
src/
├── core/                  # 🔥 核心引擎层
│   ├── events/            # 事件系统
│   │   ├── event_bus.py   # 事件总线实现
│   │   └── event_types.py # 事件类型定义
│   ├── audio_manager.py   # 音频管理器
│   ├── operation_controller.py # 操作控制器
│   └── service_manager.py # 服务管理器
│
├── interfaces/            # 📱 多界面支持层
│   ├── cli/               # CLI界面实现
│   │   └── cli_interface.py
│   └── grpc/              # gRPC接口（待开发）
│       └── generated/     # gRPC生成代码
│
├── dialogue/              # 💬 对话管理层
│   ├── dialogue_manager.py # 对话管理器
│   ├── session_manager.py  # 会话管理器
│   └── message.py         # 消息模型
│
├── llm/                   # 🤖 大语言模型集成
│   ├── base.py            # LLM基类
│   ├── openai_llm.py      # OpenAI兼容实现
│   └── enhanced_llm.py    # 增强LLM功能
│
├── asr/                   # 🎯 语音识别层
│   ├── base.py            # ASR基类
│   └── aliyun_asr.py      # 阿里云ASR实现
│
├── tts/                   # 🎤 语音合成层
│   ├── base.py            # TTS基类
│   └── aliyun_tts.py      # 阿里云TTS实现
│
└── utils/                 # 🛠️ 工具层
    ├── config/            # 配置管理
    │   └── config_manager.py
    ├── audio/             # 音频工具
    │   └── audio_player.py
    ├── logging/           # 日志管理
    │   └── logging_config.py
    └── helpers/           # 通用助手工具
```

### 架构特点
- **事件驱动**: 基于事件总线的异步架构，支持松耦合的组件通信
- **模块化设计**: 每个功能模块独立，便于维护和扩展
- **多界面支持**: 统一的操作抽象层，支持CLI、gRPC等多种接口
- **会话管理**: 完整的对话和会话存储功能，支持上下文记忆
- **异步处理**: 全面支持异步I/O，提升性能和响应性

## 关键配置

### 配置文件结构 (config/config.json)
```json
{
  "LOCAL_ASR": {
    "ENABLED": true,
    "PROVIDER": "aliyun",
    "ALIYUN_ASR": {
      "access_key_id": "",
      "access_key_secret": "", 
      "token": "...",
      "app_key": "...",
      "sample_rate": 16000,
      "channels": 1,
      "bits": 16,
      "format": "pcm"
    }
  },
  "LOCAL_TTS": {
    "ENABLED": true,
    "PROVIDER": "aliyun",
    "ALIYUN_TTS": {
      "access_key_id": "",
      "access_key_secret": "",
      "token": "...",
      "app_key": "...",
      "sample_rate": 16000,
      "format": "pcm",
      "voice": "zhixiaobai",
      "volume": 50,
      "speech_rate": 0,
      "pitch_rate": 0
    }
  },
  "LLM": {
    "ENABLED": true,
    "PROVIDER": "openai",
    "OPENAI_LLM": {
      "api_key": "sk-...",
      "base_url": "https://api.siliconflow.cn/v1",
      "model": "Qwen/Qwen3-30B-A3B",
      "max_tokens": 2000,
      "temperature": 0.7
    }
  }
}
```

### 个性化配置 (config/personality.yaml)
配置AI助手的个性特征和行为模式，支持角色定制。

### 数据存储
- **会话数据**: `data/sessions/` - JSON格式的会话记录
- **日志文件**: `src/logs/app.log` - 应用运行日志
- **会话索引**: `data/sessions/sessions_index.json` - 会话元数据索引

### LLM服务配置要点
- 支持所有OpenAI兼容的API服务（SiliconFlow、DeepSeek、通义千问等）
- `base_url` 可指向本地部署的LLM服务
- 超时时间设为60秒以适应大模型响应
- 自动处理SOCKS代理环境变量冲突

## 开发注意事项

### 事件系统使用
```python
# 事件发布
from src.core.events.event_bus import event_bus
from src.core.events.event_types import AudioStartEvent

event_bus.publish(AudioStartEvent(source="cli"))

# 事件监听
from src.core.events.event_bus import event_handler

@event_handler("audio.start")
async def handle_audio_start(event):
    print(f"音频开始事件: {event}")
```

### 重要导入路径
由于项目采用模块化结构，注意使用正确的导入路径：
```python
# 配置管理
from src.utils.config.config_manager import ConfigManager

# 日志配置
from src.utils.logging.logging_config import setup_logging

# 音频播放
from src.utils.audio.audio_player import AudioPlayer

# 事件系统
from src.core.events.event_bus import event_bus
from src.core.events.event_types import *

# 对话管理
from src.dialogue.dialogue_manager import DialogueManager
from src.dialogue.session_manager import SessionManager
```

### 异步编程模式
- 所有网络请求使用async/await
- 音频处理采用事件驱动模式
- 服务间通过事件总线解耦通信
- 配置管理器支持全局访问

### 扩展新功能
1. **ASR/TTS**: 继承对应基类，实现异步接口
2. **LLM**: 继承`LLMProviderBase`，实现chat方法
3. **界面**: 在`src/interfaces/`下新增界面实现
4. **事件**: 在`event_types.py`中定义新事件类型

### 依赖库关键点
- `sounddevice`: 跨平台音频I/O，音频录制和播放
- `numpy`: 音频数据处理和格式转换
- `aiohttp/websockets`: 异步网络通信
- `openai`: LLM API客户端
- `colorlog`: 彩色日志输出
- `pyyaml`: YAML配置文件解析
- `uuid`: 会话和消息唯一标识生成

## 项目文件结构

### 核心文件说明
- `main.py`: 应用程序入口，初始化所有服务
- `pyproject.toml`: 现代Python项目配置（uv支持）
- `requirements.txt`: 传统依赖声明文件
- `uv.lock`: uv依赖锁定文件

### 目录功能
- `config/`: 配置文件目录
- `data/sessions/`: 会话数据存储
- `src/logs/`: 应用日志输出
- `proto/`: gRPC协议定义文件
- `scripts/`: 开发和测试脚本
- `tests/`: 测试代码
- `docs/`: 项目文档

## 开发流程建议

### 新功能开发
1. **需求分析**: 明确功能需求和接口设计
2. **事件定义**: 在`event_types.py`中定义相关事件
3. **模块实现**: 在对应目录下实现功能模块
4. **事件集成**: 通过事件总线集成到主流程
5. **测试验证**: 编写单元测试和集成测试

### 调试技巧
- 使用`src/logs/app.log`查看详细日志
- 事件总线支持事件追踪和调试
- 配置文件支持动态重载（部分配置）
- 会话数据可直接查看JSON文件内容

### 性能优化
- 事件处理采用异步模式，避免阻塞
- 音频数据流式处理，减少内存占用
- LLM请求支持超时和重试机制
- 会话存储采用增量更新策略