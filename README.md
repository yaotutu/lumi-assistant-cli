# lumi-assistant

极简AI语音助手，专为CLI环境设计。

## 功能特性

- 🎯 语音识别 (ASR) - 阿里云语音识别
- 🤖 智能对话 (LLM) - OpenAI兼容API
- 🎤 语音合成 (TTS) - 阿里云语音合成
- 💬 对话管理 - 支持会话历史
- 🎙️ 实时音频 - 基于sounddevice

## 快速开始

```bash
# 安装依赖
uv sync

# 运行助手
uv run python main.py
```

## 配置

项目会在首次运行时自动生成 `config/config.json` 配置文件，请根据需要修改相关API密钥。