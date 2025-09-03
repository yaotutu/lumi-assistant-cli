# lumi-assistant 目录结构重构方案

## 📊 当前目录结构分析

### 🔍 现状
```
lumi-assistant/
├── main.py                    # ❌ 过于臃肿，包含所有逻辑
├── config/config.json         # ✅ 配置文件位置合理
├── src/
│   ├── asr/                   # ✅ 现有模块结构清晰
│   ├── llm/                   # ✅ 新增模块，结构良好
│   ├── tts/                   # ✅ 现有模块结构清晰
│   └── utils/                 # ⚠️ 功能过于杂乱，需要拆分
├── docs/                      # ✅ 文档目录
└── test_llm.py               # ⚠️ 测试脚本应该组织化
```

### 🔧 存在的问题

1. **main.py 过于复杂** - 包含音频处理、用户交互、流程控制等所有逻辑
2. **缺少核心引擎层** - 没有统一的事件系统和操作控制器
3. **utils 目录混乱** - 配置、日志、音频播放功能混在一起
4. **缺少新架构模块** - intent、mcp、grpc、core等模块目录不存在
5. **测试组织不当** - 测试文件散落在根目录

## 🎯 目标目录结构

### 📁 重构后的理想结构

```
lumi-assistant/
├── main.py                          # 🔄 简化的启动入口
├── config/                          # ⚙️ 配置目录
│   ├── config.json                 # 主配置文件
│   ├── intent_config.yaml          # 意图配置
│   └── mcp_tools.json              # MCP工具配置
├── proto/                          # 🌐 gRPC协议定义
│   ├── lumi.proto                  # 协议定义文件
│   └── generated/                  # 生成的gRPC代码
│       ├── lumi_pb2.py
│       ├── lumi_pb2_grpc.py
│       └── __init__.py
├── src/                            # 📦 核心源码
│   ├── core/                       # 🔥 核心引擎层
│   │   ├── __init__.py
│   │   ├── events/                 # 事件系统
│   │   │   ├── __init__.py
│   │   │   ├── event_bus.py        # 事件总线
│   │   │   ├── event_types.py      # 事件类型定义
│   │   │   └── handlers/           # 事件处理器
│   │   │       ├── __init__.py
│   │   │       ├── audio_handler.py
│   │   │       └── text_handler.py
│   │   ├── audio_engine.py         # 音频处理引擎
│   │   ├── conversation_manager.py # 对话管理器
│   │   └── operation_controller.py # 操作控制器
│   │
│   ├── intent/                     # 🧠 意图识别层
│   │   ├── __init__.py
│   │   ├── base.py                 # 意图识别基类
│   │   ├── llm_intent.py           # LLM意图识别器
│   │   ├── intent_router.py        # 意图路由器
│   │   └── handlers/               # 意图处理器
│   │       ├── __init__.py
│   │       ├── chat_handler.py     # 闲聊处理器
│   │       ├── tool_handler.py     # 工具调用处理器
│   │       └── command_handler.py  # 命令处理器
│   │
│   ├── mcp/                        # 🔧 MCP工具调用层
│   │   ├── __init__.py
│   │   ├── mcp_client.py           # MCP协议客户端
│   │   ├── tool_manager.py         # 工具管理器
│   │   ├── tool_executor.py        # 工具执行器
│   │   ├── tool_registry.py        # 工具注册表
│   │   └── tools/                  # MCP工具实现
│   │       ├── __init__.py
│   │       ├── system_tools.py     # 系统工具
│   │       └── iot_tools.py        # IoT工具
│   │
│   ├── iot/                        # 🏠 IoT设备控制层
│   │   ├── __init__.py
│   │   ├── device_manager.py       # 设备管理器
│   │   ├── device_discovery.py     # 设备发现
│   │   ├── device_controller.py    # 设备控制器
│   │   ├── device_status.py        # 设备状态管理
│   │   └── devices/                # 具体设备实现
│   │       ├── __init__.py
│   │       ├── smart_lamp.py       # 智能灯
│   │       └── smart_speaker.py    # 智能音响
│   │
│   ├── grpc/                       # 🌐 gRPC接口层
│   │   ├── __init__.py
│   │   ├── grpc_server.py          # gRPC服务器
│   │   ├── grpc_client.py          # gRPC客户端
│   │   ├── service_impl.py         # 服务实现
│   │   └── interceptors/           # 拦截器
│   │       ├── __init__.py
│   │       ├── auth_interceptor.py
│   │       └── logging_interceptor.py
│   │
│   ├── interfaces/                 # 📱 界面抽象层
│   │   ├── __init__.py
│   │   ├── base_interface.py       # 接口基类
│   │   ├── cli_interface.py        # CLI接口
│   │   └── grpc_interface.py       # gRPC接口适配
│   │
│   ├── dialogue/                   # 💬 对话管理层
│   │   ├── __init__.py
│   │   ├── conversation.py         # 对话会话
│   │   ├── history_manager.py      # 历史管理
│   │   ├── context_manager.py      # 上下文管理
│   │   └── storage/                # 存储层
│   │       ├── __init__.py
│   │       ├── sqlite_storage.py   # SQLite存储
│   │       └── memory_storage.py   # 内存存储
│   │
│   ├── llm/                        # 🤖 LLM集成层 (现有)
│   ├── asr/                        # 🎯 语音识别层 (现有)
│   ├── tts/                        # 🎤 语音合成层 (现有)
│   │
│   └── utils/                      # 🛠️ 工具层 (重构)
│       ├── __init__.py
│       ├── config/                 # 配置管理
│       │   ├── __init__.py
│       │   └── config_manager.py
│       ├── logging/                # 日志管理
│       │   ├── __init__.py
│       │   └── logging_config.py
│       ├── audio/                  # 音频工具
│       │   ├── __init__.py
│       │   └── audio_player.py
│       └── helpers/                # 通用助手
│           ├── __init__.py
│           ├── file_utils.py
│           └── time_utils.py
│
├── tests/                          # 🧪 测试目录
│   ├── __init__.py
│   ├── unit/                       # 单元测试
│   │   ├── test_llm.py
│   │   ├── test_asr.py
│   │   └── test_tts.py
│   ├── integration/                # 集成测试
│   │   ├── test_conversation.py
│   │   └── test_grpc_api.py
│   └── e2e/                        # 端到端测试
│       └── test_full_flow.py
│
├── examples/                       # 📚 示例和演示
│   ├── cli_client.py               # CLI客户端示例
│   ├── grpc_client.py              # gRPC客户端示例
│   └── gui_client.py               # GUI客户端示例(未来)
│
├── scripts/                        # 🔧 脚本目录
│   ├── setup.py                    # 环境设置脚本
│   ├── generate_proto.py           # Protocol Buffer生成脚本
│   └── migrate_data.py             # 数据迁移脚本
│
├── docs/                           # 📖 文档目录
│   ├── api/                        # API文档
│   ├── architecture/               # 架构文档
│   └── user_guide/                 # 用户指南
│
└── [项目文件]                      # 项目配置文件
    ├── requirements.txt
    ├── requirements-dev.txt        # 开发依赖
    ├── setup.py                    # 包安装配置
    ├── pyproject.toml              # 项目元数据
    ├── .gitignore
    ├── TODO.md
    ├── CLAUDE.md
    ├── DEVELOPMENT_PLAN.md
    └── MISSING_FEATURES.md
```

## 🔄 重构实施方案

### 阶段一：创建新目录结构 (无破坏性)

1. **创建核心目录**
```bash
mkdir -p src/core/{events,handlers}
mkdir -p src/intent/handlers
mkdir -p src/mcp/tools
mkdir -p src/iot/devices
mkdir -p src/grpc/interceptors
mkdir -p src/interfaces
mkdir -p src/dialogue/storage
mkdir -p proto/generated
mkdir -p tests/{unit,integration,e2e}
mkdir -p examples scripts
```

2. **重构utils目录**
```bash
mkdir -p src/utils/{config,logging,audio,helpers}
```

### 阶段二：代码迁移 (渐进式)

#### 2.1 创建事件系统基础设施
- [ ] 创建 `src/core/events/event_bus.py`
- [ ] 创建 `src/core/events/event_types.py` 
- [ ] 定义基础事件类型

#### 2.2 拆分main.py逻辑
- [ ] 提取音频处理到 `src/core/audio_engine.py`
- [ ] 创建对话管理器 `src/core/conversation_manager.py`
- [ ] 创建操作控制器 `src/core/operation_controller.py`
- [ ] 简化main.py为启动入口

#### 2.3 重构utils模块
- [ ] 移动配置管理到 `src/utils/config/`
- [ ] 移动日志配置到 `src/utils/logging/`
- [ ] 移动音频播放到 `src/utils/audio/`

#### 2.4 创建interface抽象层
- [ ] 创建 `src/interfaces/base_interface.py`
- [ ] 创建 `src/interfaces/cli_interface.py`
- [ ] 从main.py提取CLI逻辑

### 阶段三：新功能模块 (扩展性)

#### 3.1 意图识别模块
- [ ] 创建 `src/intent/` 完整结构
- [ ] 实现基础意图识别器

#### 3.2 MCP工具调用模块  
- [ ] 创建 `src/mcp/` 完整结构
- [ ] 实现基础MCP客户端

#### 3.3 gRPC接口模块
- [ ] 定义 `proto/lumi.proto`
- [ ] 生成Python gRPC代码
- [ ] 实现gRPC服务器

### 阶段四：测试和文档完善

#### 4.1 测试重构
- [ ] 移动现有测试到 `tests/unit/`
- [ ] 创建集成测试
- [ ] 添加端到端测试

#### 4.2 示例和脚本
- [ ] 创建客户端示例
- [ ] 添加实用脚本

## ⚠️ 重构注意事项

### 保持向后兼容
1. **分步迁移**: 不要一次性重构所有代码
2. **保留旧接口**: 在新接口稳定前保持旧接口可用
3. **渐进式重构**: 先创建新结构，再逐步迁移功能

### 模块依赖管理
1. **明确依赖层次**: core → intent/mcp → interfaces
2. **避免循环依赖**: 使用依赖注入和事件解耦
3. **接口抽象**: 通过抽象接口降低模块耦合

### 配置管理
1. **分层配置**: 按功能模块分离配置文件
2. **环境区分**: 支持开发、测试、生产环境配置
3. **配置验证**: 添加配置文件格式验证

## 🎯 重构的核心价值

### 架构清晰
- **分层明确**: 每个目录有明确的职责边界
- **模块独立**: 每个模块可以独立开发和测试
- **扩展方便**: 新功能有明确的添加位置

### 开发效率
- **代码组织**: 相关代码集中，便于查找和维护
- **测试友好**: 模块化结构便于编写单元测试
- **团队协作**: 清晰的目录结构便于多人开发

### 未来演进
- **多接口支持**: CLI、gRPC、GUI等多种接口并存
- **功能扩展**: 新功能模块有标准化的添加方式
- **平台兼容**: 支持不同部署环境和使用场景

这个重构方案将使lumi-assistant从单体应用进化为模块化、可扩展的AI助手平台！