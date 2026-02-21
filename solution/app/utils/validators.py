from fastapi import HTTPException

def validate_experiment_logic(variants: list, audience_share: float):
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