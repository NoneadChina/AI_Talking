# -*- coding: utf-8 -*-
"""
AI Talking Web应用后端服务
提供RESTful API，支持聊天、讨论、辩论、历史管理等功能
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 导入所需模块
from fastapi import FastAPI, HTTPException, Body, Depends, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt
from passlib.context import CryptContext

# 导入AI聊天管理器
from chat_between_ais import AIChatManager
from src.utils.chat_history_manager import ChatHistoryManager
from src.utils.logger_config import get_logger

# 导入错误监控模块
from error_monitor import error_monitor

# SQLite数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./ai_talking.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# JWT配置
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 用户角色枚举
class UserRole(str):
    ADMIN = "admin"
    USER = "user"

# 用户模型
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 获取用户
def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# 验证密码
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 获取密码哈希值
def get_password_hash(password):
    return pwd_context.hash(password)

# 创建访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 验证令牌
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

# 验证超级管理员权限
def is_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

# 获取日志记录器
logger = get_logger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI Talking API",
    description="AI Talking Web应用后端API服务",
    version="0.3.1"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 初始化聊天历史管理器
chat_history_manager = ChatHistoryManager()

# 响应模型定义
class ChatResponse(BaseModel):
    """
    聊天响应模型
    """
    success: bool = True
    response: str
    
class ErrorResponse(BaseModel):
    """
    错误响应模型
    """
    success: bool = False
    error: str
    detail: Optional[str] = None

class DiscussionResponse(BaseModel):
    """
    讨论响应模型
    """
    success: bool = True
    discussion_history: str

class DebateResponse(BaseModel):
    """
    辩论响应模型
    """
    success: bool = True
    debate_history: str

class HistoryListResponse(BaseModel):
    """
    历史记录列表响应模型
    """
    success: bool = True
    history_list: List[Dict[str, Any]]

class HistoryDetailResponse(BaseModel):
    """
    历史记录详情响应模型
    """
    success: bool = True
    history_detail: Dict[str, Any]

class SettingsResponse(BaseModel):
    """
    设置响应模型
    """
    success: bool = True
    api_config: Dict[str, Any]
    system_prompt: Dict[str, str]

class AboutResponse(BaseModel):
    """
    关于信息响应模型
    """
    success: bool = True
    about: Dict[str, Any]

# 认证相关请求模型
class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None

class UserCreate(BaseModel):
    """用户创建模型"""
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = UserRole.USER

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# 聊天相关请求模型
class ChatRequest(BaseModel):
    """
    聊天请求模型
    
    Args:
        message: 用户输入的消息
        api: API类型（openai, ollama, deepseek）
        model: 模型名称
        temperature: 生成温度，控制输出的随机性（0-2）
    """
    message: str
    api: str
    model: str
    temperature: float = 0.8

class DiscussionRequest(BaseModel):
    """
    讨论请求模型
    
    Args:
        topic: 讨论主题
        model1: 模型1名称
        api1: 模型1 API类型
        model2: 模型2名称
        api2: 模型2 API类型
        rounds: 讨论轮数
        time_limit: 时间限制（秒，0表示无限制）
        temperature: 生成温度
    """
    topic: str
    model1: str
    api1: str
    model2: str
    api2: str
    rounds: int = 5
    time_limit: int = 0
    temperature: float = 0.8

class DebateRequest(BaseModel):
    """
    辩论请求模型
    
    Args:
        topic: 辩论主题
        model1: 模型1名称（正方）
        api1: 模型1 API类型
        model2: 模型2名称（反方）
        api2: 模型2 API类型
        rounds: 辩论轮数
        time_limit: 时间限制（秒，0表示无限制）
        temperature: 生成温度
    """
    topic: str
    model1: str
    api1: str
    model2: str
    api2: str
    rounds: int = 5
    time_limit: int = 0
    temperature: float = 0.8

class APIConfig(BaseModel):
    """
    API配置模型
    
    Args:
        openai: OpenAI API配置
        deepseek: DeepSeek API配置
        ollama: Ollama API配置
    """
    openai: Dict[str, str]
    deepseek: Dict[str, str]
    ollama: Dict[str, str]

class SystemPrompt(BaseModel):
    """
    系统提示词模型
    
    Args:
        chat_system_prompt: 聊天系统提示词
        discussion_system_prompt: 讨论系统提示词
        discussion_ai1_system_prompt: 讨论AI1系统提示词
        discussion_ai2_system_prompt: 讨论AI2系统提示词
        debate_system_prompt: 辩论系统提示词
        debate_ai1_system_prompt: 辩论正方系统提示词
        debate_ai2_system_prompt: 辩论反方系统提示词
    """
    chat_system_prompt: str
    discussion_system_prompt: str
    discussion_ai1_system_prompt: str
    discussion_ai2_system_prompt: str
    debate_system_prompt: str
    debate_ai1_system_prompt: str
    debate_ai2_system_prompt: str

# 全局变量，用于存储AI聊天管理器实例
ai_chat_managers: Dict[str, AIChatManager] = {}

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("AI Talking后端服务已启动")
    
    # 创建或更新超级管理员用户
    db = SessionLocal()
    try:
        admin_user = get_user(db, username="admin")
        if not admin_user:
            # 创建超级管理员用户
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("超级管理员用户已创建")
        else:
            # 更新现有admin用户的角色和密码
            if admin_user.role != UserRole.ADMIN:
                admin_user.role = UserRole.ADMIN
                admin_user.hashed_password = get_password_hash("admin")
                db.commit()
                logger.info("超级管理员用户已更新")
    except Exception as e:
        logger.error(f"创建超级管理员用户失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("AI Talking后端服务已关闭")

# 认证相关API
@app.post("/api/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    获取访问令牌
    """
    user = get_user(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/users/register", response_model=UserResponse)
async def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """
    注册新用户
    """
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 检查邮箱是否已注册
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return current_user

@app.get("/api/users", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（仅管理员）
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# 聊天相关API
@app.post("/api/chat/send")
async def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    发送聊天消息
    """
    api_endpoint = "/api/chat/send"
    try:
        # 获取或创建AI聊天管理器实例
        manager_key = f"{request.api}_{request.model}"
        if manager_key not in ai_chat_managers:
            ai_chat_managers[manager_key] = AIChatManager(
                model1_name=request.model,
                model1_api=request.api,
                temperature=request.temperature
            )
        
        manager = ai_chat_managers[manager_key]
        
        # 构建消息列表
        messages = [
            {"role": "user", "content": request.message}
        ]
        
        # 获取AI响应
        response = manager.get_ai_response(
            model_name=request.model,
            messages=messages,
            api_type=request.api
        )
        
        # 添加到聊天历史
        chat_history_manager.add_history(
            topic="聊天",
            model1_name=request.model,
            model2_name="",
            api1=request.api,
            api2="",
            rounds=1,
            chat_content=f"用户: {request.message}\nAI: {response}",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return {
            "success": True,
            "response": response
        }
    except ConnectionError as e:
        error_msg = f"网络连接错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("ConnectionError", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=503, detail=error_msg)
    except TimeoutError as e:
        error_msg = f"请求超时: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("TimeoutError", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=504, detail=error_msg)
    except ValueError as e:
        error_msg = f"请求参数错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("ValueError", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=400, detail=error_msg)
    except PermissionError as e:
        error_msg = f"权限错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("PermissionError", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=403, detail=error_msg)
    except Exception as e:
        error_msg = f"服务器内部错误: {str(e)}"
        logger.error(f"发送聊天消息失败: {str(e)}")
        error_monitor.record_error("Exception", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/chat/send/stream")
async def send_chat_message_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    发送聊天消息（流式输出）
    """
    api_endpoint = "/api/chat/send/stream"
    try:
        # 获取或创建AI聊天管理器实例
        manager_key = f"{request.api}_{request.model}"
        if manager_key not in ai_chat_managers:
            ai_chat_managers[manager_key] = AIChatManager(
                model1_name=request.model,
                model1_api=request.api,
                temperature=request.temperature
            )
        
        manager = ai_chat_managers[manager_key]
        
        # 构建消息列表
        messages = [
            {"role": "user", "content": request.message}
        ]
        
        # 流式生成AI响应
        async def generate():
            full_response = ""
            # 获取AI流式响应
            async for chunk in manager.get_ai_stream_response(
                model_name=request.model,
                messages=messages,
                api_type=request.api
            ):
                # 使用Server-Sent Events (SSE)格式返回
                yield f"data: {json.dumps({'content': chunk})}\n\n"
                full_response += chunk
            
            # 添加到聊天历史
            chat_history_manager.add_history(
                topic="聊天",
                model1_name=request.model,
                model2_name="",
                api1=request.api,
                api2="",
                rounds=1,
                chat_content=f"用户: {request.message}\nAI: {full_response}",
                start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    except ConnectionError as e:
        error_msg = f"网络连接错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("ConnectionError", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=503, detail=error_msg)
    except TimeoutError as e:
        error_msg = f"请求超时: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("TimeoutError", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=504, detail=error_msg)
    except ValueError as e:
        error_msg = f"请求参数错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("ValueError", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=400, detail=error_msg)
    except PermissionError as e:
        error_msg = f"权限错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("PermissionError", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=403, detail=error_msg)
    except Exception as e:
        error_msg = f"服务器内部错误: {str(e)}"
        logger.error(f"发送聊天消息失败: {str(e)}")
        error_monitor.record_error("Exception", str(e), "chat", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/models/ollama")
async def get_ollama_models(
    current_user: User = Depends(get_current_user)
):
    """
    获取Ollama模型列表
    """
    api_endpoint = "/api/models/ollama"
    try:
        # 创建AI聊天管理器实例（仅用于获取模型列表）
        manager = AIChatManager(
            model1_name="",
            model1_api="ollama",
            temperature=0.8
        )
        
        # 获取Ollama模型列表
        models = manager.get_ollama_models()
        
        return {
            "success": True,
            "models": models
        }
    except ConnectionError as e:
        error_msg = f"网络连接错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("ConnectionError", str(e), "models", api_endpoint)
        raise HTTPException(status_code=503, detail=error_msg)
    except TimeoutError as e:
        error_msg = f"请求超时: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("TimeoutError", str(e), "models", api_endpoint)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"获取Ollama模型列表失败: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("Exception", str(e), "models", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

# 讨论相关API
@app.post("/api/discussion/start")
async def start_discussion(
    request: DiscussionRequest,
    current_user: User = Depends(get_current_user)
):
    """开始讨论"""
    api_endpoint = "/api/discussion/start"
    try:
        # 创建AI聊天管理器实例
        manager = AIChatManager(
            model1_name=request.model1,
            model2_name=request.model2,
            model1_api=request.api1,
            model2_api=request.api2,
            temperature=request.temperature
        )
        
        # 这里简化实现，实际应该启动讨论线程
        # 构建讨论历史
        discussion_history = f"主题: {request.topic}\n"
        
        # 模拟讨论过程
        for round_num in range(1, request.rounds + 1):
            discussion_history += f"\n=== 第{round_num}轮讨论 ===\n"
            
            # AI1发言
            ai1_messages = [
                {"role": "user", "content": f"主题: {request.topic}\n请发表你的观点。"}
            ]
            ai1_response = manager.get_ai_response(
                model_name=request.model1,
                messages=ai1_messages,
                api_type=request.api1
            )
            discussion_history += f"{request.model1}: {ai1_response}\n"
            
            # AI2发言
            ai2_messages = [
                {"role": "user", "content": f"主题: {request.topic}\n对方观点: {ai1_response}\n请发表你的观点。"}
            ]
            ai2_response = manager.get_ai_response(
                model_name=request.model2,
                messages=ai2_messages,
                api_type=request.api2
            )
            discussion_history += f"{request.model2}: {ai2_response}\n"
        
        # 添加到聊天历史
        chat_history_manager.add_history(
            topic=request.topic,
            model1_name=request.model1,
            model2_name=request.model2,
            api1=request.api1,
            api2=request.api2,
            rounds=request.rounds,
            chat_content=discussion_history,
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return {
            "success": True,
            "discussion_history": discussion_history
        }
    except ConnectionError as e:
        error_msg = f"网络连接错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("ConnectionError", str(e), "discussion", api_endpoint)
        raise HTTPException(status_code=503, detail=error_msg)
    except TimeoutError as e:
        error_msg = f"请求超时: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("TimeoutError", str(e), "discussion", api_endpoint)
        raise HTTPException(status_code=504, detail=error_msg)
    except ValueError as e:
        error_msg = f"请求参数错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("ValueError", str(e), "discussion", api_endpoint)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"服务器内部错误: {str(e)}"
        logger.error(f"开始讨论失败: {str(e)}")
        error_monitor.record_error("Exception", str(e), "discussion", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

# 辩论相关API
@app.post("/api/debate/start")
async def start_debate(
    request: DebateRequest,
    current_user: User = Depends(get_current_user)
):
    """开始辩论"""
    api_endpoint = "/api/debate/start"
    try:
        # 创建AI聊天管理器实例
        manager = AIChatManager(
            model1_name=request.model1,
            model2_name=request.model2,
            model1_api=request.api1,
            model2_api=request.api2,
            temperature=request.temperature
        )
        
        # 这里简化实现，实际应该启动辩论线程
        # 构建辩论历史
        debate_history = f"主题: {request.topic}\n"
        
        # 模拟辩论过程
        for round_num in range(1, request.rounds + 1):
            debate_history += f"\n=== 第{round_num}轮辩论 ===\n"
            
            # 正方发言
            ai1_messages = [
                {"role": "user", "content": f"主题: {request.topic}\n你是正方，请发表你的观点。"}
            ]
            ai1_response = manager.get_ai_response(
                model_name=request.model1,
                messages=ai1_messages,
                api_type=request.api1
            )
            debate_history += f"正方{request.model1}: {ai1_response}\n"
            
            # 反方发言
            ai2_messages = [
                {"role": "user", "content": f"主题: {request.topic}\n对方观点: {ai1_response}\n你是反方，请发表你的观点。"}
            ]
            ai2_response = manager.get_ai_response(
                model_name=request.model2,
                messages=ai2_messages,
                api_type=request.api2
            )
            debate_history += f"反方{request.model2}: {ai2_response}\n"
        
        # 添加到聊天历史
        chat_history_manager.add_history(
            topic=request.topic,
            model1_name=request.model1,
            model2_name=request.model2,
            api1=request.api1,
            api2=request.api2,
            rounds=request.rounds,
            chat_content=debate_history,
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return {
            "success": True,
            "debate_history": debate_history
        }
    except ConnectionError as e:
        error_msg = f"网络连接错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("ConnectionError", str(e), "debate", api_endpoint)
        raise HTTPException(status_code=503, detail=error_msg)
    except TimeoutError as e:
        error_msg = f"请求超时: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("TimeoutError", str(e), "debate", api_endpoint)
        raise HTTPException(status_code=504, detail=error_msg)
    except ValueError as e:
        error_msg = f"请求参数错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("ValueError", str(e), "debate", api_endpoint)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"服务器内部错误: {str(e)}"
        logger.error(f"开始辩论失败: {str(e)}")
        error_monitor.record_error("Exception", str(e), "debate", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

# 历史记录相关API
@app.get("/api/history/list")
async def get_history_list(
    current_user: User = Depends(get_current_user)
):
    """获取历史记录列表"""
    api_endpoint = "/api/history/list"
    try:
        history = chat_history_manager.load_history()
        return {
            "success": True,
            "history_list": history
        }
    except FileNotFoundError as e:
        error_msg = f"历史记录文件未找到: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("FileNotFoundError", str(e), "history", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"历史记录文件格式错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("JSONDecodeError", str(e), "history", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"获取历史记录列表失败: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("Exception", str(e), "history", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/history/detail/{index}")
async def get_history_detail(
    index: int,
    current_user: User = Depends(get_current_user)
):
    """获取历史记录详情"""
    api_endpoint = "/api/history/detail/{index}"
    try:
        history = chat_history_manager.load_history()
        if 0 <= index < len(history):
            return {
                "success": True,
                "history_detail": history[index]
            }
        else:
            error_msg = "历史记录不存在"
            logger.error(error_msg)
            error_monitor.record_error("NotFoundError", error_msg, "history", api_endpoint)
            raise HTTPException(status_code=404, detail=error_msg)
    except Exception as e:
        error_msg = f"获取历史记录详情失败: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("Exception", str(e), "history", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

@app.delete("/api/history/delete/{index}")
async def delete_history(
    index: int,
    current_user: User = Depends(get_current_user)
):
    """删除历史记录"""
    api_endpoint = "/api/history/delete/{index}"
    try:
        success = chat_history_manager.delete_history(index)
        if success:
            return {
                "success": True,
                "message": "历史记录删除成功"
            }
        else:
            error_msg = "历史记录不存在"
            logger.error(error_msg)
            error_monitor.record_error("NotFoundError", error_msg, "history", api_endpoint)
            raise HTTPException(status_code=404, detail=error_msg)
    except Exception as e:
        error_msg = f"删除历史记录失败: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("Exception", str(e), "history", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

@app.delete("/api/history/clear")
async def clear_all_history(
    current_user: User = Depends(get_current_user)
):
    """清空所有历史记录"""
    api_endpoint = "/api/history/clear"
    try:
        success = chat_history_manager.clear_history()
        if success:
            return {
                "success": True,
                "message": "所有历史记录已清空"
            }
        else:
            error_msg = "清空历史记录失败"
            logger.error(error_msg)
            error_monitor.record_error("OperationFailed", error_msg, "history", api_endpoint)
            raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"清空历史记录失败: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("Exception", str(e), "history", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

# API设置相关API
@app.post("/api/settings/save")
async def save_settings(
    api_config: APIConfig = Body(...),
    system_prompt: SystemPrompt = Body(...),
    current_user: User = Depends(is_admin)
):
    """保存API设置"""
    api_endpoint = "/api/settings/save"
    try:
        # 这里简化实现，实际应该保存到文件或数据库
        # 保存API配置到环境变量
        for key, value in api_config.openai.items():
            os.environ[f"OPENAI_{key.upper()}"] = value
        
        for key, value in api_config.deepseek.items():
            os.environ[f"DEEPSEEK_{key.upper()}"] = value
        
        for key, value in api_config.ollama.items():
            os.environ[f"OLLAMA_{key.upper()}"] = value
        
        # 保存系统提示词
        for key, value in system_prompt.dict().items():
            os.environ[f"{key.upper()}"] = value
        
        return {
            "success": True,
            "message": "设置保存成功"
        }
    except PermissionError as e:
        error_msg = f"权限错误: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("PermissionError", str(e), "settings", api_endpoint)
        raise HTTPException(status_code=403, detail=error_msg)
    except Exception as e:
        error_msg = f"保存设置失败: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("Exception", str(e), "settings", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/settings/load")
async def load_settings(
    current_user: User = Depends(get_current_user)
):
    """加载API设置"""
    api_endpoint = "/api/settings/load"
    try:
        # 加载API配置
        api_config = {
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            },
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
            },
            "ollama": {
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                "api_key": os.getenv("OLLAMA_API_KEY", "")
            }
        }
        
        # 加载系统提示词
        system_prompt = {
            "chat_system_prompt": os.getenv("CHAT_SYSTEM_PROMPT", "你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。"),
            "discussion_system_prompt": os.getenv("DISCUSSION_SYSTEM_PROMPT", ""),
            "discussion_ai1_system_prompt": os.getenv("DISCUSSION_AI1_SYSTEM_PROMPT", ""),
            "discussion_ai2_system_prompt": os.getenv("DISCUSSION_AI2_SYSTEM_PROMPT", ""),
            "debate_system_prompt": os.getenv("DEBATE_SYSTEM_PROMPT", ""),
            "debate_ai1_system_prompt": os.getenv("DEBATE_AI1_SYSTEM_PROMPT", ""),
            "debate_ai2_system_prompt": os.getenv("DEBATE_AI2_SYSTEM_PROMPT", "")
        }
        
        return {
            "success": True,
            "api_config": api_config,
            "system_prompt": system_prompt
        }
    except Exception as e:
        error_msg = f"加载设置失败: {str(e)}"
        logger.error(error_msg)
        error_monitor.record_error("Exception", str(e), "settings", api_endpoint)
        raise HTTPException(status_code=500, detail=error_msg)

# 关于页面API
@app.get("/api/about")
async def get_about_info():
    """获取关于信息"""
    return {
        "success": True,
        "about": {
            "name": "AI Talking",
            "version": "0.3.1",
            "company": "NONEAD Corporation",
            "contact": "support@nonead.com",
            "features": [
                "💬 支持与AI进行单聊",
                "🔄 支持AI之间的讨论模式",
                "⚖️ 支持AI之间的辩论模式",
                "📝 支持聊天历史管理",
                "🔧 支持多种API服务商配置"
            ]
        }
    }

# 错误监控相关API
@app.get("/api/error-monitor/statistics")
async def get_error_statistics():
    """
    获取错误统计信息
    """
    try:
        return {
            "success": True,
            "error_counts": error_monitor.get_error_counts(),
            "error_rate": error_monitor.get_error_rate(),
            "api_error_counts": error_monitor.get_api_error_counts()
        }
    except Exception as e:
        logger.error(f"获取错误统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/error-monitor/recent-errors")
async def get_recent_errors(count: int = 10):
    """
    获取最近的错误记录
    
    Args:
        count: 要获取的错误数量，默认为10
    """
    try:
        return {
            "success": True,
            "recent_errors": error_monitor.get_recent_errors(count)
        }
    except Exception as e:
        logger.error(f"获取最近错误记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/error-monitor/clear")
async def clear_error_records():
    """
    清空错误记录
    """
    try:
        error_monitor.clear_errors()
        return {
            "success": True,
            "message": "错误记录已清空"
        }
    except Exception as e:
        logger.error(f"清空错误记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI Talking后端服务运行中",
        "version": "0.3.1",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
