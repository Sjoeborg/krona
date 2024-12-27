"""Classes for corporate actions (Split, Spinoff, Rename)
Represents a corporate action, immutable and with minimal logic
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CorporateActionType(Enum):
    SPLIT = "split"
    SPINOFF = "spinoff"
    RENAME = "rename"


@dataclass
class CorporateAction:
    """Represents a corporate action, immutable and with minimal logic"""

    date: datetime
    action_type: CorporateActionType
    old_symbol: str
    new_symbol: str
    ratio: float | None = None  # For splits and spinoffs
