"""
FastAPI 后端服务器
提供 SSE 流式输出的 AI 聊天接口
"""
import asyncio
import json
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv

from chat_service import ChatService
from config import get_settings
from models import ChatRequest, ChatResponse, HealthResponse, ErrorResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取配置
settings = get_settings()

# 全局聊天服务实例
chat_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global chat_service
    
    # 启动时初始化
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
async def http_exception_handler(request, exc):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "服务器内部错误", "detail": str(exc)}
    )


@app.get("/")
async def root():
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
async def health_check():
    """健康检查"""
    is_healthy = chat_service is not None and chat_service.initialized
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
async def stream_chat(request: ChatRequest):
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

