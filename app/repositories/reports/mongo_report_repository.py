from bson import ObjectId
from bson.decimal128 import Decimal128

from app.database.mongodb import MongoDB
from app.repositories.reports.report_repository import ReportRepository

SPACE_STATUSES = ("available", "occupied", "reserved", "out_of_service")

# Joins each group with its parking document to expose the name and city.
PARKING_LOOKUP = [
    {"$lookup": {"from": "parkings", "localField": "parking_id", "foreignField": "_id", "as": "parking"}},
    {"$unwind": {"path": "$parking", "preserveNullAndEmptyArrays": True}},
]


def _id(value):
    if not ObjectId.is_valid(value):
        raise ValueError("Identificador inválido")
    return ObjectId(value)


def _count_when(status):
    return {"$sum": {"$cond": [{"$eq": ["$status", status]}, 1, 0]}}


class MongoReportRepository(ReportRepository):
    async def occupancy_by_parking(self, parking_id=None):
        """Current number of spaces per status for each parking."""
        pipeline = []
        if parking_id:
            pipeline.append({"$match": {"parking_id": _id(parking_id)}})
        pipeline += [
            {"$group": {
                "_id": "$parking_id",
                "total_spaces": {"$sum": 1},
                **{status: _count_when(status) for status in SPACE_STATUSES},
            }},
            {"$addFields": {"parking_id": "$_id"}},
            *PARKING_LOOKUP,
            {"$project": {
                "_id": 0,
                "parking_id": 1,
                "parking_name": "$parking.name",
                "city": "$parking.city",
                "total_spaces": 1,
                "by_status": {status: f"${status}" for status in SPACE_STATUSES},
                # Share of the spaces in service that are occupied right now.
                "occupancy_rate": {"$let": {
                    "vars": {"in_service": {"$subtract": ["$total_spaces", "$out_of_service"]}},
                    "in": {"$cond": [
                        {"$gt": ["$$in_service", 0]},
                        {"$round": [{"$multiply": [{"$divide": ["$occupied", "$$in_service"]}, 100]}, 2]},
                        0,
                    ]},
                }},
            }},
            {"$sort": {"parking_name": 1, "parking_id": 1}},
        ]
        cursor = await MongoDB.get_database()["parking_spaces"].aggregate(pipeline)
        return [self._serialize(item) async for item in cursor]

    async def revenue_by_parking(self, date_from, date_to, parking_id=None):
        """Revenue of the sessions completed in [date_from, date_to) per parking and currency."""
        match = {"status": "completed", "exit_at": {"$gte": date_from, "$lt": date_to}}
        if parking_id:
            match["parking_id"] = _id(parking_id)
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": {"parking_id": "$parking_id", "currency": "$tariff_snapshot.currency"},
                "revenue": {"$sum": "$total_amount"},
                "completed_sessions": {"$sum": 1},
                "average_duration_minutes": {"$avg": "$duration_minutes"},
            }},
            {"$addFields": {"parking_id": "$_id.parking_id"}},
            *PARKING_LOOKUP,
            {"$project": {
                "_id": 0,
                "parking_id": 1,
                "parking_name": "$parking.name",
                "city": "$parking.city",
                "currency": "$_id.currency",
                "revenue": 1,
                "completed_sessions": 1,
                "average_duration_minutes": {"$round": ["$average_duration_minutes", 2]},
            }},
            {"$sort": {"revenue": -1, "parking_id": 1}},
        ]
        cursor = await MongoDB.get_database()["parking_sessions"].aggregate(pipeline)
        return [self._serialize(item) async for item in cursor]

    @staticmethod
    def _serialize(item):
        item["parking_id"] = str(item["parking_id"])
        if isinstance(item.get("revenue"), Decimal128):
            item["revenue"] = item["revenue"].to_decimal()
        return item
