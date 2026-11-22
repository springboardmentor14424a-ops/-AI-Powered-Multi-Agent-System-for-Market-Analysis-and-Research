from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WatchlistCreate(BaseModel):
    symbol: str
    name: Optional[str] = None


class WatchlistItem(BaseModel):
    id: int
    symbol: str
    name: Optional[str] = None
    created_at: datetime
    price: Optional[float] = None
    change: Optional[float] = None
    changePercent: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class RecentSearchCreate(BaseModel):
    symbol: str
    name: Optional[str] = None


class RecentSearchItem(BaseModel):
    id: int
    symbol: str
    name: Optional[str] = None
    searched_at: datetime

    model_config = ConfigDict(from_attributes=True)
