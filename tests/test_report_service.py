from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.services.reportservice.report_errors import ReportError
from app.services.reportservice.report_service_impl import ReportServiceImpl

DATE_FROM = datetime(2026, 11, 1, tzinfo=timezone.utc)
DATE_TO = datetime(2026, 12, 1, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_occupancy_delegates_to_repository():
    repository = AsyncMock()
    repository.occupancy_by_parking.return_value = [{"parking_id": "abc", "total_spaces": 10}]
    service = ReportServiceImpl(repository)

    result = await service.occupancy(parking_id="abc")

    assert result == [{"parking_id": "abc", "total_spaces": 10}]
    repository.occupancy_by_parking.assert_awaited_once_with(parking_id="abc")


@pytest.mark.asyncio
async def test_revenue_delegates_range_and_parking_to_repository():
    repository = AsyncMock()
    repository.revenue_by_parking.return_value = [{"parking_id": "abc", "revenue": "15000.00"}]
    service = ReportServiceImpl(repository)

    result = await service.revenue(DATE_FROM, DATE_TO, parking_id="abc")

    assert result == [{"parking_id": "abc", "revenue": "15000.00"}]
    repository.revenue_by_parking.assert_awaited_once_with(DATE_FROM, DATE_TO, parking_id="abc")


@pytest.mark.asyncio
async def test_revenue_treats_naive_dates_as_utc():
    repository = AsyncMock()
    repository.revenue_by_parking.return_value = []
    service = ReportServiceImpl(repository)

    await service.revenue(datetime(2026, 11, 1), datetime(2026, 12, 1))

    assert repository.revenue_by_parking.await_args.args == (DATE_FROM, DATE_TO)


@pytest.mark.asyncio
async def test_revenue_rejects_range_that_does_not_advance():
    repository = AsyncMock()
    service = ReportServiceImpl(repository)

    with pytest.raises(ReportError) as error:
        await service.revenue(DATE_TO, DATE_FROM)

    assert error.value.status_code == 422
    repository.revenue_by_parking.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalid_parking_id_becomes_domain_error():
    repository = AsyncMock()
    repository.occupancy_by_parking.side_effect = ValueError("Identificador inválido")
    repository.revenue_by_parking.side_effect = ValueError("Identificador inválido")
    service = ReportServiceImpl(repository)

    with pytest.raises(ReportError) as occupancy_error:
        await service.occupancy(parking_id="no-es-un-id")
    with pytest.raises(ReportError) as revenue_error:
        await service.revenue(DATE_FROM, DATE_TO, parking_id="no-es-un-id")

    assert occupancy_error.value.status_code == 422
    assert revenue_error.value.status_code == 422


@pytest.mark.asyncio
async def test_reports_are_unavailable_without_a_report_repository():
    service = ReportServiceImpl(None)

    with pytest.raises(ReportError) as occupancy_error:
        await service.occupancy()
    with pytest.raises(ReportError) as revenue_error:
        await service.revenue(DATE_FROM, DATE_TO)

    assert occupancy_error.value.status_code == 501
    assert revenue_error.value.status_code == 501
