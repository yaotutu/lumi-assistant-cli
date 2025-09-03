# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

lumi-assistant 是一个极简AI语音助手，专为CLI环境设计。实现了完整的语音交互流程：语音识别(ASR) → 大语言模型处理(LLM) → 语音合成(TTS) → 音频播放。主要基于阿里云语音服务和OpenAI兼容的LLM API。

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

## 项目发展规划

### 📋 开发路线图
项目正在从简单语音助手向企业级AI助手平台演进，分6个阶段实施：

#### 🏗️ 第一阶段：核心架构重构 ✅ 已完成
**目标**：建立事件驱动架构，支持多种接口（CLI、gRPC、GUI）

**已完成的改造**：
- **✅ 事件系统**: 统一事件总线 `src/core/events/`，支持发布-订阅模式
- **✅ 操作抽象**: CLI按键('b','e') ↔ gRPC调用 ↔ GUI按钮的统一映射
- **✅ 目录重构**: 模块按功能重新组织，导入路径已更新
- **✅ 测试验证**: 程序运行正常，所有组件初始化成功

```python
# 统一操作接口设计
event_bus.publish(StartListeningEvent())  # 'b'键 / 按住按钮 / gRPC调用
event_bus.publish(StopListeningEvent())   # 'e'键 / 松开按钮 / gRPC调用
```

#### 🧠 第二阶段：智能功能增强 ⭐⭐⭐⭐⭐
**目标**：实现真正的AI助手能力

**核心功能**：
- **意图识别**: `src/intent/` - 基于LLM的用户意图分析和路由
- **MCP工具调用**: `src/mcp/` - 完整的MCP协议客户端，支持外部工具集成
- **函数调用**: LLM支持OpenAI function calling格式

#### 🌐 第三阶段：gRPC接口实现 ⭐⭐⭐⭐
**目标**：提供标准化的远程调用接口

**核心组件**：
- **协议定义**: `proto/lumi.proto` - gRPC服务和消息定义
- **双向流**: 支持实时状态更新和事件推送
- **客户端SDK**: Python客户端库，便于GUI等应用集成

### 🏛️ 当前架构实现状态

```
lumi-assistant/
├── main.py                    # 🚀 启动入口 ✅ (运行正常)
├── config/                    # ⚙️ 配置文件 ✅
│   └── config.json           # 主配置文件 (自动生成)
├── proto/generated/           # 🌐 gRPC生成代码 (待添加)
├── src/
│   ├── core/                  # 🔥 核心引擎层 ✅ 已实现
│   │   ├── events/            # 事件系统 ✅
│   │   │   ├── event_bus.py   # 事件总线 (完整实现)
│   │   │   └── event_types.py # 事件类型定义 (音频/系统/对话事件)
│   │   └── operation_controller.py # 操作控制器 ✅
│   │
│   ├── intent/                # 🧠 意图识别层 (第二阶段)
│   ├── mcp/                   # 🔧 MCP工具调用层 (第二阶段)  
│   ├── grpc/                  # 🌐 gRPC接口层 (第三阶段)
│   ├── interfaces/            # 📱 多界面支持层 (第三阶段)
│   ├── dialogue/              # 💬 高级对话管理 (第五阶段)
│   ├── iot/                   # 🏠 IoT设备控制 (第四阶段)
│   │
│   ├── llm/                   # 🤖 LLM集成层 ✅ (OpenAI兼容API)
│   ├── asr/                   # 🎯 语音识别层 ✅ (阿里云ASR)
│   ├── tts/                   # 🎤 语音合成层 ✅ (阿里云TTS)
│   └── utils/                 # 🛠️ 工具层 ✅ 已重构
│       ├── config/            # 配置管理 ✅
│       ├── logging/           # 日志管理 ✅
│       ├── audio/             # 音频工具 ✅
│       └── helpers/           # 通用助手 (待扩展)
│
├── tests/                     # 🧪 测试目录 ✅ 已重构
│   ├── unit/                  # 单元测试 (test_llm.py等)
│   ├── integration/           # 集成测试 (待添加)
│   └── e2e/                   # 端到端测试 (待添加)
│
└── examples/                  # 📚 示例目录 ✅ 已准备
```

**✅ 第一阶段完成状态**：
- 目录结构重构 100% 完成
- 事件驱动架构基础设施已就绪
- 所有导入路径已更新，程序运行正常
- ASR、LLM、TTS 全部组件正常初始化

### 🎯 架构设计原则

#### 事件驱动模式
所有用户操作通过事件系统统一处理，支持：
- CLI按键操作 ('b' 开始录音, 'e' 停止录音)  
- gRPC远程调用
- 未来的GUI按钮操作

#### 操作抽象层
```python
class OperationController:
    async def start_listening(self):
        # 可被CLI/gRPC/GUI任意方式触发
        
    async def stop_listening(self):
        # 统一的停止逻辑
```

#### 插件化扩展
- 意图处理器插件化
- MCP工具动态注册
- 设备控制器可扩展

### 📝 开发文档参考
- `DEVELOPMENT_PLAN.md`: 详细的分阶段开发计划
- `MISSING_FEATURES.md`: 与服务端项目的功能差距分析
- `TODO.md`: 具体任务清单和进度跟踪

### 🔧 重构进展和导入路径更新

#### 已完成的重构
1. **✅ 事件系统**: 已实现完整的事件总线和事件类型定义
2. **✅ 操作控制器**: 统一的操作接口，支持多种触发方式
3. **✅ 目录重构**: utils模块已按功能重新组织
4. **✅ 测试重组**: 测试文件已移至规范的tests目录

#### 重要导入路径变更
由于目录结构重构，以下导入路径已更新：
```python
# 旧路径 → 新路径
from src.utils.config_manager import ConfigManager
# ↓ 
from src.utils.config.config_manager import ConfigManager

from src.utils.logging_config import setup_logging
# ↓
from src.utils.logging.logging_config import setup_logging

from src.utils.audio_player import AudioPlayer  
# ↓
from src.utils.audio.audio_player import AudioPlayer
```

#### 新增核心模块使用方式
```python
# 事件系统使用
from src.core.events.event_bus import event_bus
from src.core.events.event_types import StartListeningEvent

# 操作控制器使用
from src.core.operation_controller import operation_controller

# 事件处理器装饰器
from src.core.events.event_bus import event_handler

@event_handler("audio.start_listening")
async def handle_start_listening(event):
    print(f"开始录音事件来自: {event.source}")
```

### ⚠️ 重构注意事项
1. **保持向后兼容**: 重构过程中确保现有功能正常
2. **渐进式改造**: 按模块逐步重构，避免大范围破坏性改动
3. **事件系统优先**: 先建立事件基础设施，再迁移具体功能
4. **接口抽象**: 为每个核心操作定义清晰的抽象接口
5. **导入路径**: 注意更新导入路径以匹配新的目录结构

### 🔮 长期愿景
将lumi-assistant发展为支持多种前端的AI助手平台：
- 命令行客户端 (现有)
- gRPC API服务 (规划中)
- 桌面GUI应用 (未来)
- Web界面 (可扩展)
- 移动端支持 (可扩展)