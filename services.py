from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from typing import List, Optional, Tuple
import datetime

from database import User, Group, Template, Broadcast, RequestLog
from models import TemplateSchema

class UserService:
    @staticmethod
    async def get_or_create(session: AsyncSession, user_id: int, username: Optional[str] = None) -> User:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(id=user_id, username=username)
            session.add(user)
            await session.commit()
        else:
            user.last_seen = datetime.datetime.utcnow()
            if username:
                user.username = username
            await session.commit()
        
        return user
    
    @staticmethod
    async def get_all_users(session: AsyncSession) -> List[User]:
        result = await session.execute(select(User))
        return result.scalars().all()
    
    @staticmethod
    async def count_users(session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).select_from(User))
        return result.scalar()

class GroupService:
    @staticmethod
    async def get_or_create(session: AsyncSession, chat_id: int, title: str) -> Group:
        result = await session.execute(select(Group).where(Group.chat_id == chat_id))
        group = result.scalar_one_or_none()
        
        if not group:
            group = Group(chat_id=chat_id, title=title)
            session.add(group)
            await session.commit()
        else:
            group.last_seen = datetime.datetime.utcnow()
            group.title = title
            await session.commit()
        
        return group
    
    @staticmethod
    async def count_groups(session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).select_from(Group))
        return result.scalar()

class TemplateService:
    @staticmethod
    async def create(session: AsyncSession, data: dict) -> Template:
        template = Template(**data)
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template
    
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Template]:
        result = await session.execute(select(Template).order_by(Template.created_at.desc()))
        return result.scalars().all()
    
    @staticmethod
    async def get_paginated(session: AsyncSession, page: int = 0, per_page: int = 10) -> Tuple[List[Template], int]:
        total = await session.execute(select(func.count()).select_from(Template))
        total_count = total.scalar()
        
        result = await session.execute(
            select(Template)
            .order_by(Template.created_at.desc())
            .offset(page * per_page)
            .limit(per_page)
        )
        
        return result.scalars().all(), (total_count + per_page - 1) // per_page
    
    @staticmethod
    async def get_by_id(session: AsyncSession, template_id: int) -> Optional[Template]:
        result = await session.execute(select(Template).where(Template.id == template_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_key(session: AsyncSession, key: str) -> Optional[Template]:
        result = await session.execute(select(Template).where(Template.template_key == key))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete(session: AsyncSession, template_id: int) -> bool:
        result = await session.execute(delete(Template).where(Template.id == template_id))
        await session.commit()
        return result.rowcount > 0

class BroadcastService:
    @staticmethod
    async def create_log(session: AsyncSession, admin_id: int, mode: str) -> Broadcast:
        broadcast = Broadcast(admin_id=admin_id, mode=mode)
        session.add(broadcast)
        await session.commit()
        await session.refresh(broadcast)
        return broadcast
    
    @staticmethod
    async def update_stats(session: AsyncSession, broadcast_id: int, success: int, fail: int):
        await session.execute(
            update(Broadcast)
            .where(Broadcast.id == broadcast_id)
            .values(success_count=success, fail_count=fail)
        )
        await session.commit()

class RequestLogService:
    @staticmethod
    async def log(session: AsyncSession, user_id: int, action: str):
        log = RequestLog(user_id=user_id, action=action)
        session.add(log)
        await session.commit()
    
    @staticmethod
    async def count_today(session: AsyncSession) -> int:
        today = datetime.datetime.utcnow().date()
        result = await session.execute(
            select(func.count())
            .select_from(RequestLog)
            .where(func.date(RequestLog.timestamp) == today)
        )
        return result.scalar()
