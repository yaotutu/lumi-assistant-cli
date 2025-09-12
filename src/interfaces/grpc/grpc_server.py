#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gRPC服务器
启动和管理gRPC服务
"""

import asyncio
import grpc
from grpc import aio
from src.utils.logging.logging_config import get_logger
from .grpc_interface import LumiAssistantServicer
from .generated import lumi_pb2_grpc

logger = get_logger(__name__)


class GRPCServer:
    """gRPC服务器管理器"""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.host = host
        self.port = port
        self.server = None
        self.servicer = None
        self.running = False
    
    async def start(self):
        """启动gRPC服务器"""
        try:
            # 创建服务器
            self.server = aio.server()
            
            # 创建服务实例
            self.servicer = LumiAssistantServicer()
            
            # 添加服务到服务器
            lumi_pb2_grpc.add_LumiAssistantServicer_to_server(
                self.servicer, self.server
            )
            
            # 绑定端口
            listen_addr = f"{self.host}:{self.port}"
            self.server.add_insecure_port(listen_addr)
            
            # 启动服务器
            await self.server.start()
            self.running = True
            
            logger.info(f"🚀 gRPC服务器已启动: {listen_addr}")
            print(f"🚀 gRPC服务器已启动: {listen_addr}")
            print("=" * 60)
            print("📡 gRPC服务就绪！")
            print("   可以开始接收客户端请求")
            print("   按 Ctrl+C 停止服务器")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"gRPC服务器启动失败: {e}")
            print(f"❌ gRPC服务器启动失败: {e}")
            return False
    
    async def stop(self):
        """停止gRPC服务器"""
        if self.server and self.running:
            logger.info("正在停止gRPC服务器...")
            print("\n🛑 正在停止gRPC服务器...")
            
            # 优雅关闭
            await self.server.stop(grace=5.0)
            self.running = False
            
            logger.info("gRPC服务器已停止")
            print("✅ gRPC服务器已停止")
    
    async def wait_for_termination(self):
        """等待服务器终止"""
        if self.server:
            await self.server.wait_for_termination()
    
    def is_running(self) -> bool:
        """检查服务器是否运行中"""
        return self.running


# 全局gRPC服务器实例
grpc_server = GRPCServer()


async def run_grpc_server(host: str = "localhost", port: int = 50051):
    """运行gRPC服务器的主函数"""
    server = GRPCServer(host, port)
    
    try:
        # 启动服务器
        if not await server.start():
            return False
        
        # 等待终止信号
        await server.wait_for_termination()
        
    except KeyboardInterrupt:
        logger.info("接收到中断信号")
        print("\n⚠️ 接收到中断信号")
        
    except Exception as e:
        logger.error(f"gRPC服务器运行错误: {e}")
        print(f"❌ gRPC服务器运行错误: {e}")
        
    finally:
        # 停止服务器
        await server.stop()
    
    return True