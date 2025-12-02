"""
数据库操作层
提供会话和消息的 CRUD 操作
"""
import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, delete, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import Session, Message


class DatabaseManager:
    """数据库管理类，提供所有数据库操作"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_session(self, title: str = "新对话") -> Session:
        """创建新会话
        
        Args:
            title: 会话标题，默认为"新对话"
            
        Returns:
            创建的会话对象
        """
        new_session = Session(title=title)
        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)
        return new_session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取单个会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话对象，如果不存在则返回 None
        """
        result = await self.db.execute(
            select(Session)
            .options(selectinload(Session.messages))
            .where(Session.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_sessions(self, limit: int = 100) -> List[Session]:
        """获取所有会话列表，按更新时间倒序
        
        Args:
            limit: 返回的最大会话数量
            
        Returns:
            会话列表
        """
        result = await self.db.execute(
            select(Session)
            .order_by(desc(Session.updated_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_session_title(self, session_id: str, title: str) -> bool:
        """更新会话标题
        
        Args:
            session_id: 会话 ID
            title: 新标题
            
        Returns:
            是否更新成功
        """
        result = await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(title=title, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话及其所有消息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否删除成功
        """
        result = await self.db.execute(
            delete(Session).where(Session.id == session_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str
    ) -> Message:
        """添加消息到会话
        
        Args:
            session_id: 会话 ID
            role: 角色 ('user' 或 'assistant')
            content: 消息内容
            
        Returns:
            创建的消息对象
        """
        new_message = Message(
            session_id=session_id,
            role=role,
            content=content
        )
        self.db.add(new_message)
        
        # 更新会话的 updated_at 时间
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(updated_at=datetime.utcnow())
        )
        
        await self.db.commit()
        await self.db.refresh(new_message)
        return new_message
    
    async def get_session_messages(
        self, 
        session_id: str, 
        limit: int = 20
    ) -> List[Message]:
        """获取会话的最近 N 条消息
        
        Args:
            session_id: 会话 ID
            limit: 返回的最大消息数量（最近的 N 条）
            
        Returns:
            消息列表，按时间顺序排列
        """
        # 先获取最近的 limit 条消息（倒序）
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(desc(Message.timestamp))
            .limit(limit)
        )
        messages = list(result.scalars().all())
        
        # 反转列表，使其按时间正序排列
        return list(reversed(messages))
    
    async def get_first_user_message(self, session_id: str) -> Optional[Message]:
        """获取会话的第一条用户消息（用于生成标题）
        
        Args:
            session_id: 会话 ID
            
        Returns:
            第一条用户消息，如果不存在则返回 None
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .where(Message.role == "user")
            .order_by(Message.timestamp)
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def export_session_json(self, session_id: str) -> Optional[str]:
        """导出会话为 JSON 格式
        
        Args:
            session_id: 会话 ID
            
        Returns:
            JSON 字符串，如果会话不存在则返回 None
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        export_data = {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in session.messages
            ]
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    async def export_session_markdown(self, session_id: str) -> Optional[str]:
        """导出会话为 Markdown 格式
        
        Args:
            session_id: 会话 ID
            
        Returns:
            Markdown 字符串，如果会话不存在则返回 None
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        lines = [
            f"# {session.title}",
            "",
            f"**创建时间**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**更新时间**: {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]
        
        for msg in session.messages:
            role_name = "用户" if msg.role == "user" else "AI 助手"
            time_str = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            lines.append(f"## {role_name} ({time_str})")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    async def count_session_messages(self, session_id: str) -> int:
        """统计会话的消息数量
        
        Args:
            session_id: 会话 ID
            
        Returns:
            消息数量
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
        )
        return len(list(result.scalars().all()))

