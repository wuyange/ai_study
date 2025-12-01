"""
FastAPI 后端服务器
提供 SSE 流式输出的 AI 聊天接口
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv

from chat_service import ChatService
from config import get_settings, Settings
from models import (
    ChatRequest, ChatResponse, HealthResponse, ErrorResponse,
    SessionCreate, SessionResponse, SessionList, MessageResponse,
    ChatRequestWithSession, UpdateSessionTitle, ExportFormat, ExportResponse
)
from database import get_db, init_db, AsyncSessionLocal, Session as DBSession, Message as DBMessage
from db_operations import DatabaseManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取配置
settings: Settings = get_settings()

# 全局聊天服务实例
chat_service: Optional[ChatService] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期管理"""
    global chat_service
    
    # 启动时初始化数据库
    logger.info("正在初始化数据库...")
    try:
        await init_db()
        logger.info("✓ 数据库初始化完成")
    except Exception as e:
        logger.error(f"✗ 数据库初始化失败: {str(e)}")
        raise
    
    # 启动时初始化 AutoGen 聊天服务
    logger.info("正在初始化 AutoGen 聊天服务...")
    try:
        chat_service = ChatService(settings)
        await chat_service.initialize()
        logger.info("✓ AutoGen 聊天服务初始化完成")
    except Exception as e:
        logger.error(f"✗ 初始化失败: {str(e)}")
        raise
    
    yield
    
    # 关闭时清理
    logger.info("正在关闭聊天服务...")
    try:
        await chat_service.cleanup()
        logger.info("✓ 聊天服务已关闭")
    except Exception as e:
        logger.error(f"清理资源时出错: {str(e)}")


# 创建 FastAPI 应用
app = FastAPI(
    title="AI Chat API",
    description="基于 AutoGen 的 AI 聊天 API，支持 SSE 流式输出",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "服务器内部错误", "detail": str(exc)}
    )


@app.get("/")
async def root() -> Dict[str, Any]:
    """根路径"""
    return {
        "message": "AI Chat API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "stream": "/api/chat/stream"
        }
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """健康检查"""
    is_healthy: bool = chat_service is not None and chat_service.initialized
    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        service="chat-api",
        autogen_initialized=is_healthy,
        version="1.0.0"
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """非流式聊天接口"""
    if not chat_service or not chat_service.initialized:
        logger.error("聊天服务未初始化")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="聊天服务未初始化"
        )
    
    try:
        logger.info(f"收到聊天请求: {request.message[:50]}...")
        response = await chat_service.chat(request.message)
        logger.info(f"聊天响应: {response[:50]}...")
        return ChatResponse(content=response)
    except Exception as e:
        logger.error(f"聊天失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天失败: {str(e)}"
        )


async def event_generator(message: str) -> AsyncGenerator[str, None]:
    """SSE 事件生成器"""
    if not chat_service or not chat_service.initialized:
        logger.error("聊天服务未初始化")
        yield f"data: {json.dumps({'error': '聊天服务未初始化'})}\n\n"
        return
    
    try:
        logger.info(f"开始流式聊天: {message[:50]}...")
        chunk_count = 0
        
        async for chunk in chat_service.stream_chat(message):
            # 发送数据块
            yield f"data: {json.dumps({'content': chunk, 'role': 'assistant'})}\n\n"
            chunk_count += 1
            # 添加小延迟以避免数据过快
            await asyncio.sleep(settings.stream_delay)
        
        logger.info(f"流式聊天完成，共发送 {chunk_count} 个数据块")
        # 发送完成标志
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_message = f"流式聊天错误: {str(e)}"
        logger.error(error_message, exc_info=True)
        yield f"data: {json.dumps({'error': error_message})}\n\n"


@app.post("/api/chat/stream")
async def stream_chat(request: ChatRequest) -> StreamingResponse:
    """SSE 流式聊天接口"""
    if not chat_service or not chat_service.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="聊天服务未初始化"
        )
    
    return StreamingResponse(
        event_generator(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
            "Content-Type": "text/event-stream",
        }
    )


# ============= 会话管理 API =============

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate) -> SessionResponse:
    """创建新会话"""
    async with AsyncSessionLocal() as db:
        db_manager = DatabaseManager(db)
        session = await db_manager.create_session(title=request.title or "新对话")
        
        return SessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0
        )


@app.get("/api/sessions", response_model=SessionList)
async def get_sessions() -> SessionList:
    """获取所有会话列表"""
    async with AsyncSessionLocal() as db:
        db_manager = DatabaseManager(db)
        sessions = await db_manager.get_all_sessions(limit=100)
        
        session_responses = []
        for session in sessions:
            msg_count = await db_manager.count_session_messages(session.id)
            session_responses.append(SessionResponse(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=msg_count
            ))
        
        return SessionList(
            sessions=session_responses,
            total=len(session_responses)
        )


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """获取单个会话详情"""
    async with AsyncSessionLocal() as db:
        db_manager = DatabaseManager(db)
        session = await db_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        msg_count = len(session.messages)
        
        return SessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=msg_count
        )


@app.put("/api/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    request: UpdateSessionTitle
) -> Dict[str, Any]:
    """更新会话标题"""
    async with AsyncSessionLocal() as db:
        db_manager = DatabaseManager(db)
        success = await db_manager.update_session_title(session_id, request.title)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        return {"success": True, "message": "标题更新成功"}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str) -> Dict[str, Any]:
    """删除会话"""
    async with AsyncSessionLocal() as db:
        db_manager = DatabaseManager(db)
        success = await db_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        return {"success": True, "message": "会话删除成功"}


@app.get("/api/sessions/{session_id}/export", response_model=ExportResponse)
async def export_session(
    session_id: str,
    format: ExportFormat = ExportFormat.JSON
) -> ExportResponse:
    """导出会话"""
    async with AsyncSessionLocal() as db:
        db_manager = DatabaseManager(db)
        
        if format == ExportFormat.JSON:
            content = await db_manager.export_session_json(session_id)
            filename = f"session_{session_id}.json"
        else:  # Markdown
            content = await db_manager.export_session_markdown(session_id)
            filename = f"session_{session_id}.md"
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        return ExportResponse(
            content=content,
            format=format,
            filename=filename
        )


# ============= 消息管理 API =============

@app.get("/api/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str) -> List[MessageResponse]:
    """获取会话的所有消息"""
    async with AsyncSessionLocal() as db:
        db_manager = DatabaseManager(db)
        messages = await db_manager.get_session_messages(session_id, limit=1000)
        
        return [
            MessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            )
            for msg in messages
        ]


@app.post("/api/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat_with_session(
    session_id: str,
    request: ChatRequest
) -> ChatResponse:
    """发送消息（非流式，带上下文）"""
    if not chat_service or not chat_service.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="聊天服务未初始化"
        )
    
    async with AsyncSessionLocal() as db:
        db_manager = DatabaseManager(db)
        
        # 1. 验证会话存在
        session = await db_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 2. 获取历史消息（最近 20 条）
        history = await db_manager.get_session_messages(session_id, limit=20)
        
        # 3. 保存用户消息
        await db_manager.add_message(session_id, "user", request.message)
        
        # 4. 调用 AI（带上下文）
        try:
            response_content = await chat_service.chat_with_context(request.message, history)
            
            # 5. 保存 AI 回复
            await db_manager.add_message(session_id, "assistant", response_content)
            
            return ChatResponse(content=response_content)
            
        except Exception as e:
            logger.error(f"聊天失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"聊天失败: {str(e)}"
            )


async def event_generator_with_session(
    session_id: str,
    message: str
) -> AsyncGenerator[str, None]:
    """带会话的 SSE 事件生成器"""
    if not chat_service or not chat_service.initialized:
        logger.error("聊天服务未初始化")
        yield f"data: {json.dumps({'error': '聊天服务未初始化'})}\n\n"
        return
    
    accumulated_content = ""
    
    try:
        async with AsyncSessionLocal() as db:
            db_manager = DatabaseManager(db)
            
            # 1. 验证会话存在
            session = await db_manager.get_session(session_id)
            if not session:
                yield f"data: {json.dumps({'error': '会话不存在'})}\n\n"
                return
            
            # 2. 获取历史消息
            history = await db_manager.get_session_messages(session_id, limit=20)
            
            # 3. 保存用户消息
            await db_manager.add_message(session_id, "user", message)
        
        # 4. 流式调用 AI（带上下文）
        logger.info(f"开始流式聊天（会话: {session_id}）: {message[:50]}...")
        chunk_count = 0
        
        async for chunk in chat_service.stream_chat_with_context(message, history):
            accumulated_content += chunk
            yield f"data: {json.dumps({'content': chunk, 'role': 'assistant'})}\n\n"
            chunk_count += 1
            await asyncio.sleep(settings.stream_delay)
        
        logger.info(f"流式聊天完成，共发送 {chunk_count} 个数据块")
        
        # 5. 保存完整的 AI 回复
        async with AsyncSessionLocal() as db:
            db_manager = DatabaseManager(db)
            await db_manager.add_message(session_id, "assistant", accumulated_content)
        
        # 发送完成标志
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_message = f"流式聊天错误: {str(e)}"
        logger.error(error_message, exc_info=True)
        yield f"data: {json.dumps({'error': error_message})}\n\n"


@app.post("/api/sessions/{session_id}/chat/stream")
async def stream_chat_with_session(
    session_id: str,
    request: ChatRequest
) -> StreamingResponse:
    """发送消息（流式，带上下文）"""
    if not chat_service or not chat_service.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="聊天服务未初始化"
        )
    
    return StreamingResponse(
        event_generator_with_session(session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
        }
    )


@app.post("/api/sessions/{session_id}/generate-title")
async def generate_session_title(session_id: str) -> Dict[str, Any]:
    """基于首条消息生成会话标题"""
    if not chat_service or not chat_service.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="聊天服务未初始化"
        )
    
    async with AsyncSessionLocal() as db:
        db_manager = DatabaseManager(db)
        
        # 获取首条用户消息
        first_message = await db_manager.get_first_user_message(session_id)
        if not first_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话中没有用户消息"
            )
        
        # 生成标题
        try:
            title = await chat_service.generate_title(first_message.content)
            
            # 更新会话标题
            await db_manager.update_session_title(session_id, title)
            
            return {"success": True, "title": title}
            
        except Exception as e:
            logger.error(f"标题生成失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"标题生成失败: {str(e)}"
            )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"正在启动服务器: http://{settings.host}:{settings.port}")
    logger.info(f"使用模型: {settings.model_name}")
    logger.info(f"允许的 CORS 源: {settings.cors_origins_list}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )

