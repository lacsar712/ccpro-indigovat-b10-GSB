"""染缸状态业务规则。"""

from decimal import Decimal
from typing import Optional

from app.models import DipLot, Vat

READY_REDOX_THRESHOLD = Decimal("-500")


class VatRuleError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def fmt_redox(value) -> str:
    """电位显示用：去掉 Decimal 尾随零（-520.00 -> -520）。"""
    return format(Decimal(value).normalize(), "f")


def ready_block_reason(latest: Optional[DipLot]) -> Optional[str]:
    """达标函数：最新批次 redoxMv 已填且 <= -500 mV 时返回 None，否则返回未达标原因。

    放行提示与改状态入口共用它；只读，绝不改写染缸状态字段。
    """
    if latest is None:
        return "尚无浸染批次"
    if latest.redoxMv is None:
        return "最新浸染批次未填氧化还原电位"
    if Decimal(latest.redoxMv) > READY_REDOX_THRESHOLD:
        return f"最新浸染批次电位 {fmt_redox(latest.redoxMv)} mV 高于 -500 mV"
    return None


def assert_can_mark_ready(latest: Optional[DipLot]) -> None:
    """不能将染缸标为 ready，除非最新浸染批次 redoxMv 已填且 <= -500。"""
    reason = ready_block_reason(latest)
    if reason is not None:
        raise VatRuleError(f"无法设为可染色：{reason}。")


def validate_vat_status_change(vat: Vat, new_status: str, latest: Optional[DipLot]) -> None:
    if new_status not in (Vat.STATUS_IDLE, Vat.STATUS_REDUCING, Vat.STATUS_READY):
        raise VatRuleError(f"未知缸状态：{new_status}")
    if new_status == Vat.STATUS_READY:
        assert_can_mark_ready(latest)
