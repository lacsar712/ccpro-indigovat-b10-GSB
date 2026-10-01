"""染缸状态业务规则。"""

from decimal import Decimal
from typing import Optional

from app.models import DipLot, Vat

READY_REDOX_THRESHOLD_MV = Decimal("-500")


class VatRuleError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def can_mark_ready(latest: Optional[DipLot]) -> bool:
    """达标判定：最新浸染批次 redoxMv 已填且 <= -500 mV。

    放行提示与「改状态」入口共用的同一个达标函数，
    任何一侧都不得另写一套门槛，也不得借此改动状态字段。
    """
    return (
        latest is not None
        and latest.redoxMv is not None
        and Decimal(latest.redoxMv) <= READY_REDOX_THRESHOLD_MV
    )


def assert_can_mark_ready(latest: Optional[DipLot]) -> None:
    """不能将染缸标为 ready，除非最新浸染批次 redoxMv 已填且 <= -500。"""
    if not can_mark_ready(latest):
        raise VatRuleError(
            "无法设为可染色：最新浸染批次的氧化还原电位为空或高于 -500 mV。"
        )


def validate_vat_status_change(vat: Vat, new_status: str, latest: Optional[DipLot]) -> None:
    valid = {Vat.STATUS_IDLE, Vat.STATUS_REDUCING, Vat.STATUS_READY}
    if new_status not in valid:
        raise VatRuleError(f"未知状态：{new_status}")
    if new_status == Vat.STATUS_READY:
        assert_can_mark_ready(latest)
