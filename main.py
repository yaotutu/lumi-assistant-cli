#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
lumi-assistant - AI语音助手
使用事件驱动架构，支持多种接口扩展
"""

import asyncio
from src.utils.logging.logging_config import setup_logging, get_logger
from src.core.audio_manager import audio_manager
from src.core.service_manager import service_manager
from src.interfaces.cli_interface import cli_interface

logger = get_logger(__name__)


async def main():
    """主函数"""
    try:
        # 设置日志
        setup_logging()
        
        # 显示欢迎信息
        cli_interface.show_welcome()
        
        # 初始化服务
        if not await service_manager.initialize_all():
            print("❌ 程序初始化失败")
            return
            
        # 初始化音频系统
        if not await audio_manager.initialize():
            print("❌ 音频系统初始化失败")
            return
        
        # 运行CLI界面
        await cli_interface.run()
        
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        logger.error(f"主程序错误: {e}", exc_info=True)
        
    finally:
        # 清理资源
        await audio_manager.cleanup()
        print("✅ 程序已退出")


if __name__ == "__main__":
    # 运行程序
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        logger.error(f"主程序错误: {e}", exc_info=True)