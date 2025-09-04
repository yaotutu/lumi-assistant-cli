# lumi-assistant - AI语音助手

## 项目概述

lumi-assistant 是一个极简AI语音助手，专为CLI环境设计。项目实现了完整的语音交互流程：
语音识别(ASR) → 大语言模型处理(LLM) → 语音合成(TTS) → 音频播放。

主要技术栈：
- 阿里云语音服务(ASR/TTS)
- OpenAI兼容的LLM API
- Python异步编程(asyncio)
- 事件驱动架构

## 项目架构

```
lumi-assistant/
├── main.py                 # 应用入口
├── requirements.txt        # 依赖包列表
├── config/                 # 配置文件目录
├── src/                    # 源代码目录
│   ├── core/               # 核心组件
│   │   ├── events/         # 事件系统
│   │   ├── audio_manager.py # 音频管理
│   │   ├── service_manager.py # 服务管理
│   │   └── operation_controller.py # 操作控制
│   ├── asr/                # 语音识别模块
│   ├── llm/                # 大语言模型集成
│   ├── tts/                # 语音合成模块
│   ├── interfaces/         # 用户接口
│   │   └── cli/            # 命令行接口
│   └── utils/              # 工具模块
├── tests/                  # 测试目录
├── docs/                   # 文档目录
├── data/                   # 数据目录
└── CLAUDE.md               # Claude使用指南
```

## 核心组件

### 事件驱动架构
项目采用事件驱动架构，核心组件包括：
- `EventBus`: 事件总线，实现发布-订阅模式
- `EventManager`: 事件管理器，处理各种系统事件
- `OperationController`: 操作控制器，统一处理用户操作

### 音频处理
- `AudioManager`: 音频管理器，负责录音和播放
- `AudioPlayer`: 音频播放器，支持PCM和WAV格式

### 服务管理
- `ServiceManager`: 服务管理器，初始化和管理ASR、LLM、TTS服务

### 用户接口
- `CLIInterface`: 命令行接口，处理用户输入和显示输出

## 配置管理

配置文件位于 `config/config.json`，支持以下主要配置段：
- `LOCAL_ASR`: 本地语音识别配置
- `LOCAL_TTS`: 本地语音合成配置
- `LLM`: 大语言模型配置

## 常用开发命令

### 环境配置
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# 安装依赖
pip install -r requirements.txt
```

### 运行应用
```bash
# 运行主程序
python main.py
```

## 开发约定

1. **异步编程**: 项目大量使用async/await异步编程模式
2. **事件驱动**: 组件间通信通过事件总线进行
3. **模块化设计**: 功能模块化，便于扩展和维护
4. **配置管理**: 使用点记法访问配置项，如"LOCAL_ASR.ENABLED"
5. **日志记录**: 使用统一的日志记录系统

## 核心功能流程

1. **main.py**: 程序入口，初始化各组件
2. **音频录制**: 使用sounddevice捕获麦克风输入
3. **ASR识别**: 将音频数据发送到阿里云ASR服务
4. **LLM处理**: 将识别文本发送给LLM获取回复
5. **TTS合成**: 将LLM回复通过阿里云TTS转为音频
6. **音频播放**: 播放合成的语音

## 未来开发计划

根据TODO.md和MISSING_FEATURES.md文件，项目计划实现以下功能：
1. 意图识别系统
2. MCP工具调用系统
3. IoT设备控制系统
4. 高级对话管理
5. 插件和扩展系统
6. 配置和监控系统

## 测试和调试

目前项目测试结构较为简单，建议：
1. 添加单元测试覆盖核心功能
2. 实现集成测试验证完整流程
3. 添加性能测试评估响应时间