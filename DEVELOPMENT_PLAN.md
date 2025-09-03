# lumi-assistant 开发规划和架构重构方案

## 🎯 项目愿景

将 lumi-assistant 从简单的语音助手发展为支持多种接口（CLI、gRPC、GUI）的完整AI助手系统。

## 📋 分阶段TODO计划

### 🏗️ 第一阶段：核心架构重构 (优先级：⭐⭐⭐⭐⭐)

#### 1.1 事件驱动架构改造
- [ ] **重构为事件驱动模式** (2-3天)
  - [ ] 创建统一的事件系统 (`src/core/events/`)
  - [ ] 定义标准事件类型（语音开始、语音结束、文本输入等）
  - [ ] 实现事件发布-订阅机制
  - [ ] 重构现有功能为事件处理器

- [ ] **抽象操作接口** (1-2天)
  - [ ] 定义标准操作接口（开始录音、停止录音、发送文本等）
  - [ ] 创建操作抽象层，支持多种触发方式
  - [ ] 实现CLI、gRPC、GUI的统一操作映射

#### 1.2 模块化核心组件
- [ ] **语音处理核心模块** (1天)
  - [ ] 将录音逻辑从main.py分离到 `src/core/audio_engine.py`
  - [ ] 创建音频状态管理器
  - [ ] 实现音频流控制接口

- [ ] **对话管理核心** (2天)
  - [ ] 创建 `src/core/conversation_manager.py`
  - [ ] 实现ASR→LLM→TTS完整流程管理
  - [ ] 添加对话状态跟踪

### 🧠 第二阶段：智能功能增强 (优先级：⭐⭐⭐⭐⭐)

#### 2.1 意图识别系统
- [ ] **基础意图识别** (3-4天)
  - [ ] 创建 `src/intent/` 模块
  - [ ] 实现基于LLM的意图识别器
  - [ ] 定义标准意图类型（闲聊、工具调用、设备控制等）
  - [ ] 集成到对话流程中

- [ ] **意图路由器** (1-2天)
  - [ ] 实现意图→处理器的路由机制
  - [ ] 支持插件式意图处理器注册
  - [ ] 添加意图置信度评分

#### 2.2 MCP工具调用系统
- [ ] **MCP客户端实现** (4-5天)
  - [ ] 创建 `src/mcp/` 模块结构
  - [ ] 实现MCP协议客户端
  - [ ] 工具发现和注册机制
  - [ ] 工具调用执行引擎

- [ ] **LLM工具集成** (2-3天)
  - [ ] 修改LLM客户端支持函数调用
  - [ ] 实现工具调用结果处理
  - [ ] 添加工具调用链路追踪

### 🌐 第三阶段：gRPC接口实现 (优先级：⭐⭐⭐⭐)

#### 3.1 gRPC服务定义
- [ ] **协议定义** (1天)
  - [ ] 创建 `proto/lumi.proto` 文件
  - [ ] 定义核心操作接口（StartListening, StopListening, SendText等）
  - [ ] 定义事件流接口（AudioEvent, TextEvent, StatusEvent）
  - [ ] 生成Python客户端和服务端代码

#### 3.2 gRPC服务实现
- [ ] **服务端实现** (2-3天)
  - [ ] 创建 `src/grpc/` 模块
  - [ ] 实现gRPC服务器 (`grpc_server.py`)
  - [ ] 连接事件系统和gRPC接口
  - [ ] 实现双向流通信支持

- [ ] **客户端SDK** (1-2天)
  - [ ] 创建Python客户端SDK
  - [ ] 实现异步调用支持
  - [ ] 添加连接管理和重试机制

### 🏠 第四阶段：智能家居集成 (优先级：⭐⭐⭐)

#### 4.1 IoT设备管理
- [ ] **设备发现和管理** (3-4天)
  - [ ] 创建 `src/iot/` 模块
  - [ ] 实现设备自动发现机制
  - [ ] 设备能力描述和状态管理
  - [ ] 统一设备控制接口

#### 4.2 设备控制集成
- [ ] **MCP工具集成** (2天)
  - [ ] 将IoT控制包装为MCP工具
  - [ ] 实现设备状态查询工具
  - [ ] 添加场景控制功能

### 💬 第五阶段：高级对话功能 (优先级：⭐⭐⭐)

#### 5.1 对话历史和上下文
- [ ] **对话持久化** (2-3天)
  - [ ] 实现对话历史存储（SQLite/文件）
  - [ ] 上下文管理和检索
  - [ ] 多轮对话支持

#### 5.2 个性化和学习
- [ ] **用户偏好学习** (3-4天)
  - [ ] 用户行为分析
  - [ ] 个性化回复风格
  - [ ] 常用指令快捷方式

### 🔌 第六阶段：扩展性增强 (优先级：⭐⭐)

#### 6.1 插件系统
- [ ] **插件架构** (4-5天)
  - [ ] 动态插件加载机制
  - [ ] 插件生命周期管理
  - [ ] 插件API标准化

#### 6.2 监控和调试
- [ ] **系统监控** (2-3天)
  - [ ] 性能指标收集
  - [ ] 实时状态监控
  - [ ] 调试工具和日志分析

## 🏛️ 新架构设计

### 核心架构调整

```
lumi-assistant/
├── main.py                 # 简化的启动入口
├── proto/                  # gRPC协议定义
│   ├── lumi.proto
│   └── generated/          # 生成的gRPC代码
├── src/
│   ├── core/               # 🔥 核心引擎层
│   │   ├── events/         # 事件系统
│   │   │   ├── event_bus.py      # 事件总线
│   │   │   ├── event_types.py    # 事件类型定义
│   │   │   └── handlers/         # 事件处理器
│   │   ├── audio_engine.py       # 音频处理引擎
│   │   ├── conversation_manager.py # 对话管理器
│   │   └── operation_controller.py # 操作控制器
│   │
│   ├── intent/             # 🧠 意图识别层
│   │   ├── intent_detector.py    # 意图检测器
│   │   ├── intent_router.py      # 意图路由器
│   │   └── handlers/             # 意图处理器
│   │
│   ├── mcp/               # 🔧 MCP工具调用层
│   │   ├── mcp_client.py         # MCP客户端
│   │   ├── tool_manager.py       # 工具管理器
│   │   ├── tool_executor.py      # 工具执行器
│   │   └── tools/                # 具体工具实现
│   │
│   ├── iot/               # 🏠 IoT设备控制层
│   │   ├── device_manager.py     # 设备管理器
│   │   ├── device_discovery.py   # 设备发现
│   │   └── devices/              # 设备实现
│   │
│   ├── grpc/              # 🌐 gRPC接口层
│   │   ├── grpc_server.py        # gRPC服务器
│   │   ├── grpc_client.py        # gRPC客户端
│   │   └── interceptors/         # 拦截器
│   │
│   ├── interfaces/        # 📱 界面抽象层
│   │   ├── cli_interface.py      # CLI接口
│   │   ├── grpc_interface.py     # gRPC接口适配
│   │   └── base_interface.py     # 接口基类
│   │
│   ├── dialogue/          # 💬 对话管理层
│   │   ├── conversation.py       # 对话会话
│   │   ├── history_manager.py    # 历史管理
│   │   └── context_manager.py    # 上下文管理
│   │
│   ├── llm/               # 🤖 LLM集成层 (现有)
│   ├── asr/               # 🎯 语音识别层 (现有)
│   ├── tts/               # 🎤 语音合成层 (现有)
│   └── utils/             # 🛠️ 工具层 (现有)
│
└── examples/              # 示例和测试
    ├── cli_client.py           # CLI客户端示例
    ├── grpc_client.py          # gRPC客户端示例
    └── gui_client.py           # GUI客户端示例（未来）
```

### 关键设计模式

#### 1. 事件驱动架构
```python
# 统一的操作触发方式
event_bus.publish(StartListeningEvent())
event_bus.publish(StopListeningEvent()) 
event_bus.publish(TextInputEvent(text="hello"))
```

#### 2. 抽象操作接口
```python
class OperationController:
    async def start_listening(self):
        # 可以被CLI的'b'键，gRPC调用，GUI按钮触发
        
    async def stop_listening(self):
        # 可以被CLI的'e'键，gRPC调用，GUI松开触发
```

#### 3. 插件式意图处理
```python
@intent_handler("tool_call")
async def handle_tool_call(context):
    # 处理工具调用意图
    
@intent_handler("chat") 
async def handle_chat(context):
    # 处理闲聊意图
```

## 📅 开发时间估算

- **第一阶段 (架构重构)**: 1-2周
- **第二阶段 (智能增强)**: 2-3周  
- **第三阶段 (gRPC接口)**: 1-2周
- **第四阶段 (IoT集成)**: 2周
- **第五阶段 (高级对话)**: 2-3周
- **第六阶段 (扩展增强)**: 2-3周

**总计**: 约10-15周的开发周期

## 🎯 里程碑目标

### 里程碑 1 (第1-2阶段完成)
- ✅ 事件驱动的核心架构
- ✅ 基础意图识别和MCP工具调用
- ✅ 模块化的清晰结构

### 里程碑 2 (第3阶段完成)  
- ✅ 完整的gRPC API接口
- ✅ 支持多种客户端连接
- ✅ GUI开发的基础准备

### 里程碑 3 (第4-6阶段完成)
- ✅ 完整的智能助手功能
- ✅ IoT设备控制能力
- ✅ 可扩展的插件生态

这个规划将使lumi-assistant成为一个真正的企业级AI助手平台！