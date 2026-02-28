"""
邀请码工具模块
===============

提供邀请码生成和验证功能。
"""

import random
import string


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
