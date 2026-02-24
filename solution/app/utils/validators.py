from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException
from starlette import status
from app.database.models import Experiment, ExperimentStatus
from uuid import UUID

async def validate_domain_conflict(
    session: AsyncSession,
    domain_id: UUID,
    new_offset: int,
    new_share_pct: float,
    exclude_id: UUID = None
):
    new_share = int(new_share_pct * 100)
    new_end = new_offset + new_share
    
    if new_end > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Эксперимент выходит за границы домена (100%)",
                "details": {"current_end": new_end, "limit": 100}
            }
        )

    stmt = select(Experiment).where(
        and_(
            Experiment.conflict_domain_id == domain_id,
            Experiment.status.in_([ExperimentStatus.RUNNING, ExperimentStatus.APPROVED, ExperimentStatus.ON_REVIEW]),
            Experiment.id != exclude_id if exclude_id else True
        )
    )
    
    result = await session.execute(stmt)
    existing_experiments = result.scalars().all()

    for exp in existing_experiments:
        exp_share = int(exp.audience_share * 100)
        exp_start = exp.domain_offset
        exp_end = exp_start + exp_share

        if new_offset < exp_end and exp_start < new_end:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": f"Конфликт в домене: сегмент [{new_offset}% - {new_end}%] пересекается с экспериментом '{exp.name}'",
                    "details": {
                        "conflicting_experiment_id": str(exp.id),
                        "existing_segment": f"{exp_start}% - {exp_end}%"
                    }
                }
            )

def validate_experiment_logic(variants: list, audience_share: float, flag_type: str):
    if not variants:
        raise HTTPException(status_code=400, detail="Variants list cannot be empty")
    
    total_weight = sum(v.get("weight", 0) for v in variants)
    if total_weight != 100:
        raise HTTPException(
            status_code=400, 
            detail=f"Total variants weight must be 100, current: {total_weight}"
        )
    
    if not 0.0 <= audience_share <= 1.0:
        raise HTTPException(status_code=400, detail="Audience share must be between 0 and 1")

    if flag_type == "boolean":
        if len(variants) != 2:
            raise HTTPException(
                status_code=400, 
                detail="Boolean flags must have exactly 2 variants (Control and Treatment)"
            )
        for v in variants:
            val = v.get("value")
            if not isinstance(val, bool):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Variant value '{val}' is not a boolean, but flag type is boolean"
                )
    
    elif flag_type == "number":
        for v in variants:
            if not isinstance(v.get("value"), (int, float)):
                raise HTTPException(status_code=400, detail="All variant values must be numbers")