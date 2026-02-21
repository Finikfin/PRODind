import hashlib
from uuid import UUID
from typing import Optional, Dict, Any
from app.database.models import Experiment, Flag

class DecisionEngine:
    @staticmethod
    def get_user_bucket(subject_id: UUID, experiment_id: UUID) -> int:
        hash_input = f"{subject_id}:{experiment_id}".encode()
        hash_hex = hashlib.md5(hash_input).hexdigest()
        return int(hash_hex, 16) % 100

    @classmethod
    def select_variant(cls, subject_id: UUID, experiment: Experiment) -> Optional[Dict[str, Any]]:
        bucket = cls.get_user_bucket(subject_id, experiment.id)
        
        cumulative_weight = 0
        for variant in experiment.variants:
            cumulative_weight += variant.get("weight", 0)
            if bucket < cumulative_weight:
                return variant
        return None

    @classmethod
    async def decide(
        cls, 
        flag: Flag, 
        experiment: Optional[Experiment], 
        subject_id: UUID, 
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not flag.is_active:
            return {"value": flag.default_value, "reason": "flag_disabled"}

        if not experiment:
            return {"value": flag.default_value, "reason": "no_active_experiment"}

        bucket = cls.get_user_bucket(subject_id, experiment.id)
        if bucket >= (experiment.audience_share * 100):
            return {"value": flag.default_value, "reason": "not_in_audience_share"}

        from app.utils.dsl_evaluator import DSLEvaluator
        if not DSLEvaluator.evaluate(experiment.targeting_rules, attributes):
            return {"value": flag.default_value, "reason": "targeting_mismatch"}

        variant = cls.select_variant(subject_id, experiment)
        if not variant:
            return {"value": flag.default_value, "reason": "variant_not_found"}

        return {
            "value": variant["value"],
            "variant_name": variant["name"],
            "experiment_id": experiment.id,
            "reason": "experiment_match"
        }