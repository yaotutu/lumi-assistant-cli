#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gRPC接口实现
处理gRPC请求并调用operation_controller
"""

import asyncio
import grpc
from typing import AsyncIterator
from src.utils.logging.logging_config import get_logger
from src.core.operation_controller import operation_controller
from src.core.service_manager import service_manager
from .generated import lumi_pb2, lumi_pb2_grpc

logger = get_logger(__name__)


class LumiAssistantServicer(lumi_pb2_grpc.LumiAssistantServicer):
    """Lumi Assistant gRPC服务实现"""
    
    def __init__(self):
        self.version = "2.0.0"
    
    # === 当前实现的接口 ===
    
    async def StartRecording(self, request, context):
        """开始录音"""
        try:
            task_id = await operation_controller.start_recording()
            return lumi_pb2.StartRecordingResponse(
                success=True,
                task_id=task_id
            )
        except Exception as e:
            logger.error(f"StartRecording error: {e}")
            return lumi_pb2.StartRecordingResponse(
                success=False,
                error=str(e)
            )
    
    async def StopRecording(self, request, context):
        """停止录音"""
        try:
            task_id = await operation_controller.stop_recording()
            return lumi_pb2.StopRecordingResponse(
                success=True,
                task_id=task_id
            )
        except Exception as e:
            logger.error(f"StopRecording error: {e}")
            return lumi_pb2.StopRecordingResponse(
                success=False,
                error=str(e)
            )
    
    async def SendText(self, request, context):
        """发送文本"""
        try:
            task_id = await operation_controller.send_text(request.text)
            return lumi_pb2.SendTextResponse(
                success=True,
                task_id=task_id
            )
        except Exception as e:
            logger.error(f"SendText error: {e}")
            return lumi_pb2.SendTextResponse(
                success=False,
                error=str(e)
            )
    
    async def GetEventStream(self, request, context) -> AsyncIterator[lumi_pb2.ProcessEvent]:
        """获取事件流"""
        event_queue = operation_controller.subscribe_events()
        
        try:
            while True:
                # 从队列中获取事件
                event_data = await event_queue.get()
                
                # 将字典转换为protobuf消息
                event = lumi_pb2.ProcessEvent(
                    task_id=event_data["task_id"],
                    type=getattr(lumi_pb2.EventType, event_data["type"]),
                    content=event_data["content"],
                    timestamp=event_data["timestamp"]
                )
                
                yield event
                
        except Exception as e:
            logger.error(f"EventStream error: {e}")
        finally:
            # 清理订阅
            operation_controller.unsubscribe_events(event_queue)
    
    # === 会话管理接口 ===
    
    async def NewSession(self, request, context):
        """创建新会话"""
        try:
            if not hasattr(service_manager, 'llm') or not service_manager.llm:
                return lumi_pb2.NewSessionResponse(
                    success=False,
                    error="LLM service not available"
                )
            
            await service_manager.llm.new_session()
            
            # 获取当前会话信息
            info = service_manager.llm.get_current_session_info()
            session_id = info['session_id'] if info else "unknown"
            
            return lumi_pb2.NewSessionResponse(
                success=True,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"NewSession error: {e}")
            return lumi_pb2.NewSessionResponse(
                success=False,
                error=str(e)
            )
    
    async def GetSessionInfo(self, request, context):
        """获取当前会话信息"""
        try:
            if not hasattr(service_manager, 'llm') or not service_manager.llm:
                return lumi_pb2.GetSessionInfoResponse(
                    success=False,
                    error="LLM service not available"
                )
            
            info = service_manager.llm.get_current_session_info()
            if not info:
                return lumi_pb2.GetSessionInfoResponse(
                    success=False,
                    error="No active session"
                )
            
            session_info = lumi_pb2.SessionInfo(
                session_id=info['session_id'],
                created_at=info['created_at'],
                message_count=info['message_count'],
                title=info['title']
            )
            
            return lumi_pb2.GetSessionInfoResponse(
                success=True,
                session_info=session_info
            )
            
        except Exception as e:
            logger.error(f"GetSessionInfo error: {e}")
            return lumi_pb2.GetSessionInfoResponse(
                success=False,
                error=str(e)
            )
    
    async def ListSessions(self, request, context):
        """列出历史会话"""
        try:
            if not hasattr(service_manager, 'llm') or not service_manager.llm:
                return lumi_pb2.ListSessionsResponse(
                    success=False,
                    error="LLM service not available"
                )
            
            limit = request.limit if request.limit > 0 else 10
            sessions = await service_manager.llm.list_sessions(limit)
            
            session_infos = []
            for session in sessions:
                session_info = lumi_pb2.SessionInfo(
                    session_id=session['session_id'],
                    created_at=session['created_at'],
                    message_count=session.get('message_count', 0),
                    title=session.get('title', 'New Chat')
                )
                session_infos.append(session_info)
            
            return lumi_pb2.ListSessionsResponse(
                success=True,
                sessions=session_infos
            )
            
        except Exception as e:
            logger.error(f"ListSessions error: {e}")
            return lumi_pb2.ListSessionsResponse(
                success=False,
                error=str(e)
            )
    
    async def LoadSession(self, request, context):
        """加载指定会话"""
        try:
            if not hasattr(service_manager, 'llm') or not service_manager.llm:
                return lumi_pb2.LoadSessionResponse(
                    success=False,
                    error="LLM service not available"
                )
            
            if not request.session_id:
                return lumi_pb2.LoadSessionResponse(
                    success=False,
                    error="Session ID cannot be empty"
                )
            
            success = await service_manager.llm.resume_session(request.session_id)
            
            if success:
                return lumi_pb2.LoadSessionResponse(
                    success=True,
                    message="Session loaded successfully"
                )
            else:
                return lumi_pb2.LoadSessionResponse(
                    success=False,
                    error="Failed to load session"
                )
                
        except Exception as e:
            logger.error(f"LoadSession error: {e}")
            return lumi_pb2.LoadSessionResponse(
                success=False,
                error=str(e)
            )
    
    # === 系统状态接口 ===
    
    async def GetStatus(self, request, context):
        """获取系统状态"""
        try:
            status = operation_controller.get_status()
            
            return lumi_pb2.StatusResponse(
                is_recording=status['is_recording'],
                active_tasks=status['active_tasks'],
                active_clients=status['active_clients']
            )
            
        except Exception as e:
            logger.error(f"GetStatus error: {e}")
            return lumi_pb2.StatusResponse(
                is_recording=False,
                active_tasks=0,
                active_clients=0
            )
    
    async def HealthCheck(self, request, context):
        """健康检查"""
        try:
            # 检查各个服务状态
            services = []
            
            # 检查ASR服务
            asr_available = hasattr(service_manager, 'asr') and service_manager.asr is not None
            services.append(lumi_pb2.ServiceStatus(
                name="ASR",
                available=asr_available,
                status="Available" if asr_available else "Unavailable"
            ))
            
            # 检查LLM服务
            llm_available = hasattr(service_manager, 'llm') and service_manager.llm is not None
            services.append(lumi_pb2.ServiceStatus(
                name="LLM",
                available=llm_available,
                status="Available" if llm_available else "Unavailable"
            ))
            
            # 检查TTS服务
            tts_available = hasattr(service_manager, 'tts') and service_manager.tts is not None
            services.append(lumi_pb2.ServiceStatus(
                name="TTS",
                available=tts_available,
                status="Available" if tts_available else "Unavailable"
            ))
            
            # 系统是否健康（至少LLM可用）
            is_healthy = llm_available
            
            return lumi_pb2.HealthCheckResponse(
                is_healthy=is_healthy,
                message="Health check completed",
                version=self.version,
                services=services
            )
            
        except Exception as e:
            logger.error(f"HealthCheck error: {e}")
            return lumi_pb2.HealthCheckResponse(
                is_healthy=False,
                message=f"Health check failed: {str(e)}",
                version=self.version,
                services=[]
            )
    
    # === 预留的流式接口（未来实现） ===
    
    async def StreamASR(self, request_iterator, context):
        """流式语音识别（未来实现）"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('StreamASR not implemented yet')
        raise NotImplementedError('StreamASR not implemented yet')
    
    async def StreamTTS(self, request_iterator, context):
        """流式语音合成（未来实现）"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('StreamTTS not implemented yet')
        raise NotImplementedError('StreamTTS not implemented yet')
    
    async def StreamConversation(self, request_iterator, context):
        """双向流式对话（未来实现）"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('StreamConversation not implemented yet')
        raise NotImplementedError('StreamConversation not implemented yet')