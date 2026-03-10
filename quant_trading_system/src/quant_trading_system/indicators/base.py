"""
指标基类
========

定义指标的抽象接口和注册机制
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Type

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class IndicatorResult:
    """指标计算结果"""
    
    name: str
    values: dict[str, np.ndarray] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    
    def __getitem__(self, key: str) -> np.ndarray:
        return self.values[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.values
    
    @property
    def main_value(self) -> np.ndarray:
        """主要输出值"""
        if self.values:
            return list(self.values.values())[0]
        return np.array([])


class Indicator(ABC):
    """
    指标抽象基类
    
    所有技术指标都应继承此类
    """
    
    # 指标名称
    name: ClassVar[str] = "indicator"
    
    # 指标描述
    description: ClassVar[str] = ""
    
    # 指标类型
    indicator_type: ClassVar[str] = "generic"  # trend, momentum, volume, volatility
    
    # 参数定义
    params_def: ClassVar[dict[str, dict[str, Any]]] = {}
    
    # 输出字段
    outputs: ClassVar[list[str]] = ["value"]
    
    def __init__(self, **params: Any) -> None:
        """
        初始化指标
        
        Args:
            **params: 指标参数
        """
        self.params = self._validate_params(params)
        self._cache: dict[str, Any] = {}
    
    def _validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """验证并填充默认参数"""
        validated = {}
        
        for name, definition in self.params_def.items():
            if name in params:
                value = params[name]
                # 类型检查
                expected_type = definition.get("type", float)
                if not isinstance(value, expected_type):
                    try:
                        value = expected_type(value)
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"Invalid type for parameter {name}: "
                            f"expected {expected_type.__name__}"
                        )
                
                # 范围检查
                min_val = definition.get("min")
                max_val = definition.get("max")
                if min_val is not None and value < min_val:
                    raise ValueError(f"Parameter {name} must be >= {min_val}")
                if max_val is not None and value > max_val:
                    raise ValueError(f"Parameter {name} must be <= {max_val}")
                
                validated[name] = value
            else:
                # 使用默认值
                if "default" in definition:
                    validated[name] = definition["default"]
                elif definition.get("required", False):
                    raise ValueError(f"Required parameter {name} not provided")
        
        return validated
    
    @abstractmethod
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        """
        计算指标
        
        Args:
            close: 收盘价数组
            high: 最高价数组
            low: 最低价数组
            open: 开盘价数组
            volume: 成交量数组
        
        Returns:
            指标计算结果
        """
        pass
    
    def update(
        self,
        close: float,
        high: float | None = None,
        low: float | None = None,
        open: float | None = None,
        volume: float | None = None,
    ) -> dict[str, float]:
        """
        增量更新指标（可选实现）
        
        用于实时数据流的增量计算
        """
        raise NotImplementedError(
            f"Incremental update not implemented for {self.name}"
        )
    
    def reset(self) -> None:
        """重置指标状态"""
        self._cache.clear()
    
    def __repr__(self) -> str:
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.__class__.__name__}({params_str})"


class IndicatorRegistry:
    """
    指标注册表
    
    管理所有可用的指标
    """
    
    _indicators: ClassVar[dict[str, Type[Indicator]]] = {}
    
    @classmethod
    def register(cls, indicator_class: Type[Indicator]) -> Type[Indicator]:
        """注册指标"""
        name = indicator_class.name
        cls._indicators[name] = indicator_class
        logger.debug(f"Indicator registered", name=name)
        return indicator_class
    
    @classmethod
    def get(cls, name: str) -> Type[Indicator] | None:
        """获取指标类"""
        return cls._indicators.get(name)
    
    @classmethod
    def create(cls, name: str, **params: Any) -> Indicator | None:
        """创建指标实例"""
        indicator_class = cls.get(name)
        if indicator_class:
            return indicator_class(**params)
        return None
    
    @classmethod
    def list_indicators(cls) -> list[str]:
        """列出所有指标"""
        return list(cls._indicators.keys())
    
    @classmethod
    def get_info(cls, name: str) -> dict[str, Any] | None:
        """获取指标信息"""
        indicator_class = cls.get(name)
        if indicator_class:
            return {
                "name": indicator_class.name,
                "description": indicator_class.description,
                "type": indicator_class.indicator_type,
                "params": indicator_class.params_def,
                "outputs": indicator_class.outputs,
            }
        return None


def register_indicator(cls: Type[Indicator]) -> Type[Indicator]:
    """指标注册装饰器"""
    return IndicatorRegistry.register(cls)
