from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, and_
from app.database.models import Exposure, Conversion
from uuid import UUID

class StatsService:
    @staticmethod
    async def get_experiment_stats(session: AsyncSession, experiment_id: UUID, goal_type: str):
        exposure_stmt = (
            select(
                Exposure.variant_name,
                func.count(distinct(Exposure.subject_id)).label("total_users")
            )
            .where(Exposure.experiment_id == experiment_id)
            .group_by(Exposure.variant_name)
        )
        
        exposure_res = await session.execute(exposure_stmt)
        exposure_data = {row.variant_name: row.total_users for row in exposure_res}

        first_exposure_sub = (
            select(
                Exposure.subject_id,
                Exposure.variant_name,
                func.min(Exposure.timestamp).label("min_exposure_ts")
            )
            .where(Exposure.experiment_id == experiment_id)
            .group_by(Exposure.subject_id, Exposure.variant_name)
        ).subquery()

        conversion_stmt = (
            select(
                first_exposure_sub.c.variant_name,
                func.count(distinct(Conversion.subject_id)).label("converted_users")
            )
            .join(
                Conversion, 
                Conversion.subject_id == first_exposure_sub.c.subject_id
            )
            .where(
                and_(
                    Conversion.goal_type == goal_type,
                    Conversion.timestamp >= first_exposure_sub.c.min_exposure_ts
                )
            )
            .group_by(first_exposure_sub.c.variant_name)
        )
        
        conversion_res = await session.execute(conversion_stmt)
        conversion_data = {row.variant_name: row.converted_users for row in conversion_res}

        report = []
        for variant, total in exposure_data.items():
            converted = conversion_data.get(variant, 0)
            cr = (converted / total * 100) if total > 0 else 0
            report.append({
                "variant": variant,
                "total_users": total,
                "conversions": converted,
                "conversion_rate": round(cr, 2)
            })
            
        return report