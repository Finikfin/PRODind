from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
import uuid

from app.database.session import get_session
from app.database.models import Flag, Experiment, ExperimentStatus
from app.api.decide.schemas import DecideRequest, DecideResponse
from app.services.decision_engine import DecisionEngine
from app.services.exposure_service import ExposureService

router = APIRouter(prefix="/decide", tags=["Runtime Decide"])

@router.post("/", response_model=DecideResponse)
async def decide_flags(
    request: DecideRequest,
    session: AsyncSession = Depends(get_session)
):
    results = []
    
    for key in request.keys:
        stmt = select(Flag).where(Flag.key == key)
        flag_res = await session.execute(stmt)
        flag = flag_res.scalar_one_or_none()

        if not flag:
            continue

        exp_stmt = select(Experiment).where(
            Experiment.flag_id == flag.id,
            Experiment.status == ExperimentStatus.RUNNING
        )
        exp_res = await session.execute(exp_stmt)
        experiment = exp_res.scalar_one_or_none()

        decision = await DecisionEngine.decide(
            flag, experiment, request.subject_id, request.attributes
        )

        decision_id = f"dec_{uuid4().hex[:12]}"

        if decision.get("experiment_id"):
            await ExposureService.log_exposure(
                session=session,
                experiment_id=decision["experiment_id"],
                subject_id=request.subject_id,
                variant_name=decision["variant_name"],
                decision_id=decision_id
            )

        results.append({
            "key": key,
            "value": decision["value"],
            "decision_id": decision_id,
            "metadata": {
                "reason": decision["reason"],
                "experiment_id": str(decision.get("experiment_id")) if decision.get("experiment_id") else None
            }
        })

    await session.commit()
    return {"results": results}