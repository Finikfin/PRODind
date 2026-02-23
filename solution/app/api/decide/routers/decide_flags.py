from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import uuid4

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
    
    stmt = (
        select(Flag)
        .options(
            selectinload(
                Flag.experiments.and_(Experiment.status == ExperimentStatus.RUNNING)
            )
        )
        .where(Flag.key.in_(request.keys))
    )
    
    flags_res = await session.execute(stmt)
    flags = flags_res.scalars().all()
    
    flag_map = {f.key: f for f in flags}

    for key in request.keys:
        flag = flag_map.get(key)
        
        if not flag:
            continue

        experiment = flag.experiments[0] if flag.experiments else None

        decision = await DecisionEngine.decide(
            flag, experiment, request.subject_id, request.attributes
        )

        is_experiment_match = decision.get("experiment_id") is not None
        decision_id = f"dec_{uuid4().hex[:12]}" if is_experiment_match else None

        if is_experiment_match:
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
                "experiment_id": str(decision["experiment_id"]) if is_experiment_match else None,
                "variant_name": decision.get("variant_name")
            }
        })

    await session.commit()
    return {"results": results}