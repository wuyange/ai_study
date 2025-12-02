"""
数据库模型定义
使用 SQLAlchemy 定义会话和消息表
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column

Base = declarative_base()


class Session(Base):
    """会话表模型"""
    __tablename__ = 'sessions'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
    
    # 关系：一个会话有多条消息
    messages: Mapped[List["Message"]] = relationship(
        "Message", 
        back_populates="session", 
        cascade="all, delete-orphan",
        order_by="Message.timestamp"
    )
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title={self.title})>"


class Message(Base):
    """消息表模型"""
    __tablename__ = 'messages'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey('sessions.id'), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系：消息属于一个会话
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, session_id={self.session_id})>"


# 数据库引擎配置
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "backend" / "data" / "chat.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

# 创建异步引擎
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 设为 True 可以看到 SQL 语句
    future=True
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """获取数据库会话的依赖函数"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库，创建所有表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ 数据库表创建完成")

