from datetime import timezone

from app.services.reportservice.report_errors import ReportError
from app.services.reportservice.report_service import ReportService


def _as_utc(value):
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class ReportServiceImpl(ReportService):
    def __init__(self, report_repository):
        self.report_repository = report_repository

    def _repository(self):
        # Reports are MongoDB aggregations; the PostgreSQL backend does not provide them.
        if self.report_repository is None:
            raise ReportError("Los reportes solo están disponibles con el backend MongoDB", 501)
        return self.report_repository

    async def occupancy(self, parking_id=None):
        repository = self._repository()
        try:
            return await repository.occupancy_by_parking(parking_id=parking_id)
        except ValueError as exc:
            raise ReportError(str(exc), 422) from exc

    async def revenue(self, date_from, date_to, parking_id=None):
        repository = self._repository()
        date_from, date_to = _as_utc(date_from), _as_utc(date_to)
        if date_from >= date_to:
            raise ReportError("La fecha inicial debe ser anterior a la fecha final", 422)
        try:
            return await repository.revenue_by_parking(date_from, date_to, parking_id=parking_id)
        except ValueError as exc:
            raise ReportError(str(exc), 422) from exc
