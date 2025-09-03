#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI界面管理器
处理命令行用户交互
"""

import asyncio
from src.utils.logging.logging_config import get_logger
from src.core.operation_controller import operation_controller

logger = get_logger(__name__)


class CLIInterface:
    """CLI界面管理器 - 处理命令行交互"""
    
    def __init__(self):
        self.running = False
        
    def show_welcome(self):
        """显示欢迎信息"""
        print("=" * 60)
        print("🎙️  lumi-assistant AI语音助手")
        print("=" * 60)
        print("操作说明:")
        print("  b - 开始录音")
        print("  e - 结束录音并识别")
        print("  q - 退出程序")
        print("=" * 60)
        
    async def run(self):
        """运行CLI界面"""
        self.running = True
        
        print("\n✅ 系统就绪！")
        print("📍 按 'b' 开始录音\n")
        
        # 主循环
        while self.running:
            try:
                # 获取用户输入
                cmd = input().strip().lower()
                
                if cmd == 'b':
                    # 开始录音
                    await operation_controller.start_listening("cli")
                    
                elif cmd == 'e':
                    # 结束录音并识别
                    await operation_controller.stop_listening("cli")
                    print("\n📍 按 'b' 开始新的录音")
                    
                elif cmd == 'q':
                    # 退出程序
                    print("\n👋 退出程序...")
                    await operation_controller.shutdown("cli")
                    self.running = False
                    break
                    
                elif cmd == '':
                    continue  # 忽略空输入
                    
                else:
                    print(f"❓ 未知命令: {cmd}")
                    print("   使用 b:开始 / e:结束 / q:退出")
                    
                # 给异步任务一点时间
                await asyncio.sleep(0.1)
                        
            except KeyboardInterrupt:
                print("\n\n⚠️ 程序被中断")
                self.running = False
                break
            except EOFError:
                # 处理管道输入或后台运行的情况
                logger.warning("检测到EOF，程序退出")
                self.running = False
                break
            except Exception as e:
                logger.error(f"CLI界面错误: {e}")
                continue


# 全局CLI界面实例
cli_interface = CLIInterface()