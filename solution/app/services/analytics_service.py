from sqlalchemy import select, func
from app.database.models import Exposure, Conversion

class AnalyticsService:
    @staticmethod
    async def get_report(session, experiment_id, start_date, end_date):
        query = (
            select(
                Exposure.variant_name,
                func.count(Exposure.id).label("exposures"),
                func.count(func.distinct(Conversion.decision_id)).label("unique_conversions")
            )
            .outerjoin(Conversion, Exposure.decision_id == Conversion.decision_id)
            .where(Exposure.experiment_id == experiment_id)
            .where(Exposure.timestamp >= start_date)
            .where(Exposure.timestamp <= end_date)
            .group_by(Exposure.variant_name)
        )
        res = await session.execute(query)
        return [dict(row._mapping) for row in res.all()]