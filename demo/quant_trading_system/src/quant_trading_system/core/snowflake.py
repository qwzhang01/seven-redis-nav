"""
雪花ID生成器
基于Twitter Snowflake算法，支持分布式环境下的唯一ID生成
"""

import time
import threading
from typing import Optional


class SnowflakeGenerator:
    """
    雪花ID生成器

    结构：
    - 1位符号位（始终为0）
    - 41位时间戳（毫秒级，可使用约69年）
    - 10位机器ID（数据中心5位 + 机器5位）
    - 12位序列号（每毫秒最多4096个ID）
    """

    def __init__(self, datacenter_id: int = 0, machine_id: int = 0):
        """
        初始化雪花ID生成器

        Args:
            datacenter_id: 数据中心ID (0-31)
            machine_id: 机器ID (0-31)
        """
        # 配置参数
        self.datacenter_id_bits = 5
        self.machine_id_bits = 5
        self.sequence_bits = 12

        # 最大值计算
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)
        self.max_machine_id = -1 ^ (-1 << self.machine_id_bits)
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)

        # 移位配置
        self.machine_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.machine_id_bits
        self.timestamp_shift = self.sequence_bits + self.machine_id_bits + self.datacenter_id_bits

        # 验证参数
        if datacenter_id > self.max_datacenter_id or datacenter_id < 0:
            raise ValueError(f"数据中心ID必须在0-{self.max_datacenter_id}之间")
        if machine_id > self.max_machine_id or machine_id < 0:
            raise ValueError(f"机器ID必须在0-{self.max_machine_id}之间")

        self.datacenter_id = datacenter_id
        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1

        # 线程锁
        self.lock = threading.Lock()

        # 起始时间戳（2026-01-01 00:00:00 UTC）
        self.twepoch = 1735689600000

    def _current_timestamp(self) -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        """等待下一毫秒"""
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    def generate_id(self) -> int:
        """
        生成雪花ID

        Returns:
            int: 雪花ID
        """
        with self.lock:
            timestamp = self._current_timestamp()

            # 时钟回拨处理
            if timestamp < self.last_timestamp:
                raise Exception("时钟回拨异常，拒绝生成ID")

            # 同一毫秒内生成
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    timestamp = self._wait_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # 生成ID
            return ((timestamp - self.twepoch) << self.timestamp_shift) | \
                   (self.datacenter_id << self.datacenter_id_shift) | \
                   (self.machine_id << self.machine_id_shift) | \
                   self.sequence

    def parse_id(self, snowflake_id: int) -> dict:
        """
        解析雪花ID

        Args:
            snowflake_id: 雪花ID

        Returns:
            dict: 解析结果
        """
        timestamp = (snowflake_id >> self.timestamp_shift) + self.twepoch
        datacenter_id = (snowflake_id >> self.datacenter_id_shift) & self.max_datacenter_id
        machine_id = (snowflake_id >> self.machine_id_shift) & self.max_machine_id
        sequence = snowflake_id & self.max_sequence

        return {
            'timestamp': timestamp,
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp / 1000)),
            'datacenter_id': datacenter_id,
            'machine_id': machine_id,
            'sequence': sequence
        }


# 全局雪花ID生成器实例
_snowflake_instance: Optional[SnowflakeGenerator] = None


def get_snowflake_generator(datacenter_id: int = 0, machine_id: int = 0) -> SnowflakeGenerator:
    """
    获取雪花ID生成器实例（单例模式）

    Args:
        datacenter_id: 数据中心ID
        machine_id: 机器ID

    Returns:
        SnowflakeGenerator: 雪花ID生成器实例
    """
    global _snowflake_instance
    if _snowflake_instance is None:
        _snowflake_instance = SnowflakeGenerator(datacenter_id, machine_id)
    return _snowflake_instance


def generate_snowflake_id() -> int:
    """
    生成雪花ID（便捷函数）

    Returns:
        int: 雪花ID
    """
    return get_snowflake_generator().generate_id()


def parse_snowflake_id(snowflake_id: int) -> dict:
    """
    解析雪花ID（便捷函数）

    Args:
        snowflake_id: 雪花ID

    Returns:
        dict: 解析结果
    """
    return get_snowflake_generator().parse_id(snowflake_id)


# 测试代码
if __name__ == "__main__":
    # 测试雪花ID生成器
    generator = SnowflakeGenerator()

    # 生成10个ID
    for i in range(10):
        snowflake_id = generator.generate_id()
        parsed = generator.parse_id(snowflake_id)
        print(f"ID: {snowflake_id}, 解析: {parsed}")

    # 测试便捷函数
    print("\n使用便捷函数:")
    for i in range(5):
        snowflake_id = generate_snowflake_id()
        parsed = parse_snowflake_id(snowflake_id)
        print(f"ID: {snowflake_id}, 解析: {parsed}")
