import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.session import get_session
from app.database.models import Flag, Experiment, ExperimentStatus
from app.api.decide.schemas import DecideRequest, DecideResponse
from app.services.decision_engine import DecisionEngine
from app.services.runtime_logic import ExposureService, generate_decision_id

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
                Flag.experiments.and_(
                    Experiment.status.in_([ExperimentStatus.RUNNING, ExperimentStatus.PAUSED])
                )
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

        running_exps = [e for e in flag.experiments if e.status == ExperimentStatus.RUNNING]
        experiment = None
        if running_exps:
            experiment = sorted(running_exps, key=lambda x: x.created_at, reverse=True)[0]

        decision = await DecisionEngine.decide(
            flag, experiment, request.subject_id, request.attributes
        )

        is_exp = decision.get("experiment_id") is not None
        d_id = None
        
        if is_exp:
            d_id = generate_decision_id(decision["experiment_id"], request.subject_id)
            await ExposureService.log_exposure(
                session=session,
                experiment_id=decision["experiment_id"],
                subject_id=request.subject_id,
                variant_name=decision["variant_name"],
                decision_id=d_id
            )

        results.append({
            "key": key,
            "value": decision["value"],
            "decision_id": d_id,
            "metadata": {
                "reason": decision["reason"],
                "experiment_id": str(decision["experiment_id"]) if is_exp else None,
                "variant_name": decision.get("variant_name")
            }
        })

    await session.commit()
    return {"results": results}