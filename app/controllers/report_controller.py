from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import require_manager
from app.dependencies import get_report_service
from app.schemas.report_schema import OccupancyReportItem, RevenueReportItem
from app.services.reportservice.report_errors import ReportError
from app.services.reportservice.report_service import ReportService


router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(require_manager)])


@router.get("/occupancy", response_model=list[OccupancyReportItem])
async def occupancy_report(
    parking_id: str | None = None,
    service: ReportService = Depends(get_report_service),
):
    try:
        return await service.occupancy(parking_id=parking_id)
    except ReportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/revenue", response_model=list[RevenueReportItem])
async def revenue_report(
    date_from: datetime = Query(description="Inicio del rango (incluido), ISO 8601"),
    date_to: datetime = Query(description="Fin del rango (excluido), ISO 8601"),
    parking_id: str | None = None,
    service: ReportService = Depends(get_report_service),
):
    try:
        return await service.revenue(date_from, date_to, parking_id=parking_id)
    except ReportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
