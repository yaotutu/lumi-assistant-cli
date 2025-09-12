#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
lumi-assistant - AI语音助手gRPC服务器
使用事件驱动架构提供gRPC接口服务
"""

import asyncio
import argparse
from src.utils.logging.logging_config import setup_logging, get_logger
from src.core.audio_manager import audio_manager
from src.core.service_manager import service_manager
from src.interfaces.grpc.grpc_server import run_grpc_server

logger = get_logger(__name__)


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Lumi Assistant - AI语音助手gRPC服务器")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="gRPC服务器主机地址 (默认: 0.0.0.0，允许局域网访问)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=50051,
        help="gRPC服务器端口 (默认: 50051)"
    )
    args = parser.parse_args()
    
    try:
        # 设置日志
        setup_logging()
        
        # 显示欢迎信息
        print("=" * 60)
        print("🤖  lumi-assistant AI语音助手 - gRPC服务器")
        print("=" * 60)
        
        # 初始化服务
        if not await service_manager.initialize_all():
            print("❌ 程序初始化失败")
            return
            
        # 初始化音频系统
        if not await audio_manager.initialize():
            print("❌ 音频系统初始化失败")
            return
        
        # 运行gRPC服务器
        await run_grpc_server(args.host, args.port)
        
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