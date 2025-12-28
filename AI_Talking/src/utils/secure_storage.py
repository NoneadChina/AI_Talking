# -*- coding: utf-8 -*-
"""
安全存储模块
用于加密存储敏感数据，如API密钥
"""

import sys
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .logger_config import get_logger

logger = get_logger(__name__)


class SecureStorage:
    """
    安全存储类，用于加密存储敏感数据
    """
    
    def __init__(self, password: str, salt: bytes = None):
        """
        初始化安全存储
        
        Args:
            password: 加密密码
            salt: 盐值，用于生成密钥
        """
        self.salt = salt or os.urandom(16)
        self.key = self._generate_key(password)
        self.cipher_suite = Fernet(self.key)
    
    def _generate_key(self, password: str) -> bytes:
        """
        生成加密密钥
        
        Args:
            password: 加密密码
            
        Returns:
            bytes: 加密密钥
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt(self, data: str) -> str:
        """
        加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            str: 加密后的数据，空字符串返回空字符串
        """
        if not data:
            return ""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密后的数据
            
        Returns:
            str: 解密后的数据，空字符串返回空字符串，解密失败返回空字符串
        """
        if not encrypted_data:
            return ""
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"解密失败: {str(e)}")
            return ""
    
    def get_salt_str(self) -> str:
        """
        获取盐值的字符串表示
        
        Returns:
            str: 盐值的Base64编码字符串
        """
        return base64.urlsafe_b64encode(self.salt).decode()
    
    @classmethod
    def from_salt_str(cls, password: str, salt_str: str):
        """
        从盐值字符串创建SecureStorage实例
        
        Args:
            password: 加密密码
            salt_str: 盐值的Base64编码字符串
            
        Returns:
            SecureStorage: 安全存储实例
        """
        salt = base64.urlsafe_b64decode(salt_str.encode())
        return cls(password, salt)


# 全局安全存储实例
# 实际使用时应从安全的位置获取密码
# 这里使用一个默认密码，实际部署时应修改为更安全的方式
_secure_storage = None
# 确定应用程序的安装目录
if getattr(sys, "frozen", False):
    # 打包后的可执行文件所在目录
    current_dir = os.path.dirname(sys.executable)
else:
    # 开发环境下的当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.path.dirname(current_dir)  # 向上一级目录
    current_dir = os.path.dirname(current_dir)  # 再向上一级目录
_salt_file_path = os.path.join(current_dir, "salt.txt")


def init_secure_storage(password: str = "ai_talking_default_password"):
    """
    初始化全局安全存储实例
    
    Args:
        password: 加密密码
    """
    global _secure_storage
    
    try:
        # 尝试从文件读取盐值
        if os.path.exists(_salt_file_path):
            with open(_salt_file_path, "r") as f:
                salt_str = f.read().strip()
            _secure_storage = SecureStorage.from_salt_str(password, salt_str)
            logger.info("使用现有盐值初始化安全存储")
        else:
            # 创建新的安全存储实例并保存盐值
            _secure_storage = SecureStorage(password)
            with open(_salt_file_path, "w") as f:
                f.write(_secure_storage.get_salt_str())
            logger.info("创建新的安全存储实例并保存盐值")
    except Exception as e:
        logger.error(f"初始化安全存储失败: {str(e)}")
        raise


def get_secure_storage() -> SecureStorage:
    """
    获取全局安全存储实例
    
    Returns:
        SecureStorage: 安全存储实例
    """
    global _secure_storage
    if _secure_storage is None:
        init_secure_storage()
    return _secure_storage


def encrypt_data(data: str) -> str:
    """
    加密数据（便捷函数）
    
    Args:
        data: 要加密的数据
        
    Returns:
        str: 加密后的数据
    """
    return get_secure_storage().encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """
    解密数据（便捷函数）
    
    Args:
        encrypted_data: 加密后的数据
        
    Returns:
        str: 解密后的数据
    """
    return get_secure_storage().decrypt(encrypted_data)