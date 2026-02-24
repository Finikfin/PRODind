import hashlib
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.database.models import Exposure

def generate_decision_id(experiment_id: uuid.UUID, subject_id: uuid.UUID) -> str:
    key = f"{experiment_id}:{subject_id}".encode()
    return hashlib.sha256(key).hexdigest()

class ExposureService:
    @staticmethod
    async def log_exposure(
        session: AsyncSession,
        experiment_id: uuid.UUID,
        subject_id: uuid.UUID,
        variant_name: str,
        decision_id: str
    ):
        stmt = insert(Exposure).values(
            experiment_id=experiment_id,
            subject_id=subject_id,
            variant_name=variant_name,
            decision_id=decision_id
        ).on_conflict_do_nothing(index_elements=['decision_id'])
        await session.execute(stmt)