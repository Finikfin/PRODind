from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fastapi_cache.decorator import cache

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
    decisions = await _decide_cached(request, session)

    for d in decisions:
        if d["decision_id"]:
            await ExposureService.log_exposure(
                session=session,
                experiment_id=d["metadata"]["experiment_id"],
                subject_id=request.subject_id,
                variant_name=d["metadata"]["variant_name"],
                decision_id=d["decision_id"]
            )

    await session.commit()
    return {"results": decisions}


@cache(expire=60)
async def _decide_cached(
    request: DecideRequest,
    session: AsyncSession
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
            results.append({
                "key": key,
                "value": None,
                "decision_id": None,
                "is_default": True,
                "metadata": {"reason": "flag_not_found"}
            })
            continue

        running_exps = sorted(
            flag.experiments,
            key=lambda x: x.version,
            reverse=True
        )
        experiment = running_exps[0] if running_exps else None

        decision = await DecisionEngine.decide(
            flag,
            experiment,
            request.subject_id,
            request.attributes
        )

        d_id = None
        if decision.get("experiment_id"):
            d_id = generate_decision_id(
                f"{decision['experiment_id']}_v{decision['version']}",
                request.subject_id
            )

        results.append({
            "key": key,
            "value": decision["value"],
            "decision_id": d_id,
            "is_default": decision["reason"] != "experiment_match",
            "metadata": {
                "reason": decision["reason"],
                "experiment_id": decision.get("experiment_id"),
                "variant_name": decision.get("variant_name")
            }
        })

    return results