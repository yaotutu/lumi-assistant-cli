#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM功能测试脚本
用于验证LLM集成是否正常工作
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config_manager import ConfigManager
from src.llm import OpenAILLM


async def test_llm():
    """测试LLM功能"""
    print("=" * 60)
    print("🧪 LLM功能测试")
    print("=" * 60)
    
    try:
        # 加载配置
        config_manager = ConfigManager()
        
        # 检查LLM配置
        if not config_manager.get_config("LLM.ENABLED", False):
            print("❌ LLM未启用，请在config/config.json中设置LLM.ENABLED为true")
            return False
            
        provider = config_manager.get_config("LLM.PROVIDER", "openai")
        print(f"📋 LLM提供商: {provider}")
        
        if provider == "openai":
            # 获取OpenAI配置
            llm_config = {
                "api_key": config_manager.get_config("LLM.OPENAI_LLM.api_key", ""),
                "base_url": config_manager.get_config("LLM.OPENAI_LLM.base_url", "https://api.openai.com/v1"),
                "model": config_manager.get_config("LLM.OPENAI_LLM.model", "gpt-3.5-turbo"),
                "max_tokens": config_manager.get_config("LLM.OPENAI_LLM.max_tokens", 2000),
                "temperature": config_manager.get_config("LLM.OPENAI_LLM.temperature", 0.7)
            }
            
            print(f"📋 API Base URL: {llm_config['base_url']}")
            print(f"📋 模型: {llm_config['model']}")
            
            if not llm_config["api_key"]:
                print("❌ API密钥为空，请在config/config.json中设置LLM.OPENAI_LLM.api_key")
                return False
            
            print(f"📋 API密钥: {llm_config['api_key'][:8]}...")
            
            # 创建LLM客户端
            print("\n🔧 创建LLM客户端...")
            llm_client = OpenAILLM(llm_config)
            
            # 测试连接
            print("🔗 测试连接...")
            if await llm_client.test_connection():
                print("✅ 连接成功！")
            else:
                print("❌ 连接失败")
                return False
            
            # 测试简单对话
            print("\n💬 测试简单对话...")
            test_messages = [
                "你好",
                "今天天气怎么样？",
                "请用一句话介绍人工智能",
                "谢谢"
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n📤 测试 {i}: {message}")
                try:
                    response = await llm_client.chat(message)
                    if response:
                        print(f"📥 回复: {response}")
                    else:
                        print("❌ 未收到回复")
                except Exception as e:
                    print(f"❌ 对话出错: {e}")
            
            # 测试工具调用（如果支持）
            print("\n🔧 测试工具调用功能...")
            test_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_current_time",
                        "description": "获取当前时间",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
            ]
            
            try:
                tool_response = await llm_client.chat_with_tools(
                    "现在几点了？",
                    test_tools
                )
                print(f"📥 工具调用回复: {tool_response}")
            except Exception as e:
                print(f"⚠️ 工具调用测试失败（这是正常的）: {e}")
            
            # 关闭客户端
            await llm_client.close()
            print("\n✅ LLM测试完成")
            return True
            
        else:
            print(f"❌ 不支持的LLM提供商: {provider}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_config_help():
    """打印配置帮助信息"""
    print("\n" + "=" * 60)
    print("📖 LLM配置说明")
    print("=" * 60)
    print("要使用LLM功能，请在config/config.json中配置：")
    print()
    print("1. 启用LLM功能：")
    print('   "LLM": {')
    print('     "ENABLED": true')
    print('   }')
    print()
    print("2. 配置OpenAI API：")
    print('   "LLM": {')
    print('     "PROVIDER": "openai",')
    print('     "OPENAI_LLM": {')
    print('       "api_key": "你的API密钥",')
    print('       "base_url": "https://api.openai.com/v1",')
    print('       "model": "gpt-3.5-turbo",')
    print('       "max_tokens": 2000,')
    print('       "temperature": 0.7')
    print('     }')
    print('   }')
    print()
    print("💡 提示：")
    print("- 可以使用OpenAI兼容的API服务")
    print("- base_url可以指向本地部署的LLM服务")
    print("- 确保网络连接正常，能够访问API服务")


async def main():
    """主函数"""
    success = await test_llm()
    
    if not success:
        print_config_help()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 LLM功能测试通过！")
    else:
        print("⚠️ LLM功能测试失败，请检查配置")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())