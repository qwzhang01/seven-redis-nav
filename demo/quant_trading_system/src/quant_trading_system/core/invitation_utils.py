"""
邀请码工具模块
===============

提供邀请码生成和验证功能。
"""

import random
import string
from typing import Optional


class InvitationUtils:
    """邀请码工具类"""

    @staticmethod
    def generate_invitation_code(length: int = 8) -> str:
        """
        生成随机邀请码

        参数：
        - length: 邀请码长度，默认8位

        返回：
        - 邀请码字符串
        """
        # 使用大写字母和数字生成邀请码
        characters = string.ascii_uppercase + string.digits
        # 排除容易混淆的字符：0, O, 1, I, L
        characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')

        # 生成随机邀请码
        code = ''.join(random.choice(characters) for _ in range(length))
        return code

    @staticmethod
    def validate_invitation_code_format(code: str, min_length: int = 6) -> bool:
        """
        验证邀请码格式

        参数：
        - code: 邀请码
        - min_length: 最小长度

        返回：
        - 格式是否有效
        """
        if not code or len(code) < min_length:
            return False

        # 检查是否只包含大写字母和数字
        if not all(c in string.ascii_uppercase + string.digits for c in code):
            return False

        return True
