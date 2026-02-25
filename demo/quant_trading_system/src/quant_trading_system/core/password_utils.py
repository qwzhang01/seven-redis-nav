"""
密码工具模块
============

提供密码哈希生成和校验功能，使用 bcrypt 算法进行安全密码处理。
"""

import bcrypt
import logging
from typing import Union

from quant_trading_system.core.config import settings

logger = logging.getLogger(__name__)


class PasswordUtils:
    """密码工具类"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        生成密码哈希值

        参数：
        - password: 明文密码

        返回：
        - 密码哈希字符串
        """
        if not password:
            raise ValueError("密码不能为空")

        # 使用配置中的哈希轮数生成盐值并哈希密码
        salt = bcrypt.gensalt(rounds=settings.PASSWORD_HASH_ROUNDS)
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        验证密码是否匹配

        参数：
        - password: 待验证的明文密码
        - hashed_password: 存储的密码哈希值

        返回：
        - 是否匹配
        """
        if not password or not hashed_password:
            return False

        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        from quant_trading_system.core.config import settings
        if settings.debug:
            return True, "密码强度符合要求"

        """
        验证密码强度

        参数：
        - password: 待验证的密码

        返回：
        - (是否通过验证, 错误消息)
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"密码长度至少{settings.PASSWORD_MIN_LENGTH}位"

        if len(password) > 128:
            return False, "密码长度不能超过128位"

        # 检查是否包含数字
        if not any(char.isdigit() for char in password):
            return False, "密码必须包含至少一个数字"

        # 检查是否包含字母
        if not any(char.isalpha() for char in password):
            return False, "密码必须包含至少一个字母"

        # 检查是否包含特殊字符
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_chars for char in password):
            return False, "密码必须包含至少一个特殊字符"

        return True, "密码强度符合要求"

    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """
        生成随机密码

        参数：
        - length: 密码长度（默认12位）

        返回：
        - 随机生成的密码
        """
        import secrets
        import string

        if length < 8:
            length = 8
        elif length > 128:
            length = 128

        # 定义字符集
        characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # 确保密码包含各种类型的字符
        while True:
            password = ''.join(secrets.choice(characters) for _ in range(length))

            # 验证密码强度
            is_valid, _ = PasswordUtils.validate_password_strength(password)
            if is_valid:
                return password
