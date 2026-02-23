from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Exposure
import uuid

class ExposureService:
    @staticmethod
    async def log_exposure(
        session: AsyncSession,
        experiment_id: uuid.UUID,
        subject_id: uuid.UUID,
        variant_name: str,
        decision_id: str
    ):
        exposure = Exposure(
            experiment_id=experiment_id,
            subject_id=subject_id,
            variant_name=variant_name,
            decision_id=decision_id
        )
        session.add(exposure)