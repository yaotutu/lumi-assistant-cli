#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI界面管理器
处理命令行用户交互
"""

import asyncio
import json
from datetime import datetime
from typing import Optional
from src.utils.logging.logging_config import get_logger
from src.core.operation_controller import operation_controller
from src.core.service_manager import service_manager

logger = get_logger(__name__)


class CLIInterface:
    """CLI界面管理器 - 处理命令行交互"""
    
    def __init__(self):
        self.running = False
        self.commands = {
            '/help': self.cmd_help,
            '/new': self.cmd_new_session,
            '/list': self.cmd_list_sessions,
            '/load': self.cmd_load_session,
            '/clear': self.cmd_clear_session,
            '/export': self.cmd_export_session,
            '/delete': self.cmd_delete_session,
            '/info': self.cmd_session_info,
            '/text': self.cmd_text_input
        }
        
    def show_welcome(self):
        """显示欢迎信息"""
        print("=" * 60)
        print("🎙️  lumi-assistant AI语音助手")
        print("=" * 60)
        print("操作说明:")
        print("  b - 开始录音")
        print("  e - 结束录音并识别")
        print("  q - 退出程序")
        print("\n会话命令:")
        print("  /help   - 显示所有命令")
        print("  /new    - 创建新会话")
        print("  /list   - 显示历史会话")
        print("  /text   - 文本对话模式")
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
                    
                elif cmd.startswith('/'):
                    # 处理命令
                    await self.handle_command(cmd)
                    
                else:
                    print(f"❓ 未知命令: {cmd}")
                    print("   使用 b:开始 / e:结束 / q:退出")
                    print("   输入 /help 查看所有命令")
                    
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
    
    async def handle_command(self, cmd: str):
        """处理斜杠命令"""
        parts = cmd.split(maxsplit=1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else None
        
        if command in self.commands:
            try:
                await self.commands[command](args)
            except Exception as e:
                print(f"❌ 命令执行失败: {e}")
        else:
            print(f"❓ 未知命令: {command}")
            print("   输入 /help 查看所有命令")
    
    # 命令处理函数
    async def cmd_help(self, args=None):
        """显示帮助信息"""
        print("\n📚 可用命令：")
        print("=" * 50)
        print("会话管理:")
        print("  /new        - 创建新会话")
        print("  /list       - 列出历史会话")
        print("  /load <ID>  - 加载指定会话")
        print("  /clear      - 清空当前会话")
        print("  /export     - 导出当前会话")
        print("  /delete <ID>- 删除指定会话")
        print("  /info       - 显示当前会话信息")
        print("\n对话模式:")
        print("  /text       - 进入文本对话模式")
        print("\n操作按键:")
        print("  b           - 开始语音录音")
        print("  e           - 结束录音并识别")
        print("  q           - 退出程序")
        print("=" * 50)
    
    async def cmd_new_session(self, args=None):
        """创建新会话"""
        if hasattr(service_manager, 'llm') and service_manager.llm:
            await service_manager.llm.new_session()
            print("✨ 新会话已创建")
        else:
            print("❌ LLM服务未初始化")
    
    async def cmd_list_sessions(self, args=None):
        """列出历史会话"""
        if not hasattr(service_manager, 'llm') or not service_manager.llm:
            print("❌ LLM服务未初始化")
            return
        
        sessions = await service_manager.llm.list_sessions(10)
        if not sessions:
            print("📭 暂无历史会话")
            return
        
        print("\n📚 历史会话列表：")
        print("-" * 50)
        for i, session in enumerate(sessions, 1):
            created = session['created_at'][:16]  # 只显示日期和时间
            title = session.get('title', '新对话')
            print(f"{i}. [{created}] {title}")
            if session.get('preview'):
                preview = session['preview'][:60] + ("..." if len(session['preview']) > 60 else "")
                print(f"   {preview}")
        print("-" * 50)
    
    async def cmd_load_session(self, args):
        """加载指定会话"""
        if not hasattr(service_manager, 'llm') or not service_manager.llm:
            print("❌ LLM服务未初始化")
            return
        
        if not args:
            print("❌ 请指定会话ID或编号")
            print("   用法: /load <编号或ID>")
            return
        
        try:
            # 尝试作为编号处理
            index = int(args) - 1
            sessions = await service_manager.llm.list_sessions()
            if 0 <= index < len(sessions):
                session_id = sessions[index]['session_id']
            else:
                print(f"❌ 编号 {args} 超出范围")
                return
        except ValueError:
            # 作为ID使用
            session_id = args
        
        success = await service_manager.llm.resume_session(session_id)
        if success:
            print(f"✅ 会话已加载: {session_id[:8]}...")
        else:
            print(f"❌ 加载会话失败: {session_id[:8]}...")
    
    async def cmd_clear_session(self, args=None):
        """清空当前会话"""
        if hasattr(service_manager, 'llm') and service_manager.llm:
            await service_manager.llm.clear_session()
            print("🗑️ 当前会话已清空")
        else:
            print("❌ LLM服务未初始化")
    
    async def cmd_export_session(self, args=None):
        """导出当前会话"""
        if not hasattr(service_manager, 'llm') or not service_manager.llm:
            print("❌ LLM服务未初始化")
            return
        
        data = await service_manager.llm.export_session()
        if data:
            filename = f"session_{data['session_id'][:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 会话已导出到: {filename}")
        else:
            print("❌ 没有可导出的会话")
    
    async def cmd_delete_session(self, args):
        """删除指定会话"""
        if not hasattr(service_manager, 'llm') or not service_manager.llm:
            print("❌ LLM服务未初始化")
            return
        
        if not args:
            print("❌ 请指定要删除的会话ID")
            print("   用法: /delete <会话ID>")
            return
        
        success = await service_manager.llm.delete_session(args)
        if success:
            print(f"✅ 会话已删除: {args[:8]}...")
        else:
            print(f"❌ 删除失败: {args[:8]}...")
    
    async def cmd_session_info(self, args=None):
        """显示当前会话信息"""
        if not hasattr(service_manager, 'llm') or not service_manager.llm:
            print("❌ LLM服务未初始化")
            return
        
        info = service_manager.llm.get_current_session_info()
        if info:
            print("\n📊 当前会话信息：")
            print(f"  会话ID: {info['session_id'][:8]}...")
            print(f"  创建时间: {info['created_at']}")
            print(f"  消息数量: {info['message_count']}")
            print(f"  标题: {info['title']}")
        else:
            print("📭 当前没有活动会话")
    
    async def cmd_text_input(self, args=None):
        """进入文本对话模式"""
        if not hasattr(service_manager, 'llm') or not service_manager.llm:
            print("❌ LLM服务未初始化")
            return
        
        print("\n💬 进入文本对话模式（输入 /exit 退出）")
        print("-" * 50)
        
        while True:
            try:
                text = input("👤 你: ").strip()
                
                if text == '/exit':
                    print("退出文本对话模式")
                    break
                
                if not text:
                    continue
                
                # 使用流式输出
                print("🤖 Lumi: ", end="", flush=True)
                
                response = ""
                async for chunk in service_manager.llm.chat_stream(text):
                    print(chunk, end="", flush=True)
                    response += chunk
                
                print()  # 换行
                
                # 如果有TTS服务，播放语音
                if service_manager.tts and response:
                    try:
                        pcm_data = await service_manager.tts.synthesize(response)
                        if pcm_data:
                            from src.utils.audio.audio_player import AudioPlayer
                            player = AudioPlayer()
                            await player.play_pcm(pcm_data, sample_rate=16000)
                    except Exception as e:
                        logger.debug(f"TTS播放失败: {e}")
                
            except KeyboardInterrupt:
                print("\n退出文本对话模式")
                break
            except Exception as e:
                print(f"❌ 对话错误: {e}")


# 全局CLI界面实例
cli_interface = CLIInterface()