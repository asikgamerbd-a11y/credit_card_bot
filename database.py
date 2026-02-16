from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, BigInteger, String, DateTime, Integer, Text, func
import datetime

from config import config

engine = create_async_engine(config.DB_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Group(Base):
    __tablename__ = "groups"
    
    chat_id = Column(BigInteger, primary_key=True)
    title = Column(String)
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    label = Column(String, nullable=False)
    template_key = Column(String, unique=True, nullable=False)
    display_card = Column(String, nullable=False)
    default_exp = Column(String, nullable=False)  # MM/YYYY
    default_cvv = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Broadcast(Base):
    __tablename__ = "broadcasts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)
    mode = Column(String, nullable=False)  # 'text' or 'forward'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)

class RequestLog(Base):
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
