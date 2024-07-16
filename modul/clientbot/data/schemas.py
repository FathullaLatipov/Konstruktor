from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Service(BaseModel):
    service: int
    name: str
    type: str
    rate: float
    min: int
    max: int
    dripfeed: bool
    refill: bool
    category: str
    description: str = None
    compilation_time: str = None


class OrderSchema(BaseModel):
    charge: float
    start_count: int = None
    status: str
    remains: int
    currency: str


class BillStatus(BaseModel):
    value: str
    changed_date_time: datetime = Field(alias="changedDateTime")
