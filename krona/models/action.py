from dataclasses import dataclass
from datetime import date
from enum import Enum


class ActionType(Enum):
    SPLIT = "SPLIT"


@dataclass
class Action:
    date: date
    type: ActionType
    old_symbol: str
    new_symbol: str
    old_ISIN: str
    new_ISIN: str
    ratio: float
