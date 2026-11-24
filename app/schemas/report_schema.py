from decimal import Decimal

from pydantic import BaseModel


class OccupancyReportItem(BaseModel):
    parking_id: str
    parking_name: str | None = None
    city: str | None = None
    total_spaces: int
    by_status: dict[str, int]
    occupancy_rate: float


class RevenueReportItem(BaseModel):
    parking_id: str
    parking_name: str | None = None
    city: str | None = None
    currency: str | None = None
    revenue: Decimal
    completed_sessions: int
    average_duration_minutes: float | None = None
