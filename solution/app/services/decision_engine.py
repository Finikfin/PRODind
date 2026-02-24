import hashlib
from uuid import UUID
from typing import Optional, Dict, Any, List
from app.database.models import Experiment, Flag

class DecisionEngine:
    SALT = "lotty_platform_v1"

    @staticmethod
    def get_hash_bucket(seed_id: str, subject_id: str) -> int:
        hash_input = f"{subject_id}:{seed_id}:{DecisionEngine.SALT}".encode()
        hash_hex = hashlib.md5(hash_input).hexdigest()
        return int(hash_hex, 16) % 100

    @classmethod
    def select_variant(cls, seed: str, subject_id: UUID, variants: List[Any]) -> Optional[Dict[str, Any]]:
        bucket = cls.get_hash_bucket(f"{seed}_variant", str(subject_id))
        cumulative_weight = 0
        for variant in variants:
            weight = variant.weight if hasattr(variant, 'weight') else variant.get("weight", 0)
            cumulative_weight += weight
            if bucket < cumulative_weight:
                return {
                    "name": variant.name if hasattr(variant, 'name') else variant.get("name"),
                    "value": variant.value if hasattr(variant, 'value') else variant.get("value")
                }
        return None

    @classmethod
    async def decide(
        cls, 
        flag: Flag, 
        experiment: Optional[Experiment], 
        subject_id: UUID, 
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        if hasattr(flag, 'is_active') and not flag.is_active:
            return {"value": flag.default_value, "reason": "flag_disabled"}

        if not experiment:
            return {"value": flag.default_value, "reason": "no_active_experiment"}

        s_id = str(subject_id)
        exp_seed = f"{experiment.id}:v{experiment.version}"
        
        if experiment.conflict_domain_id:
            domain_bucket = cls.get_hash_bucket(str(experiment.conflict_domain_id), s_id)
            lower_bound = experiment.domain_offset
            share_pct = int(experiment.audience_share * 100)
            upper_bound = lower_bound + share_pct
            if upper_bound <= 100:
                in_domain = lower_bound <= domain_bucket < upper_bound
            else:
                in_domain = domain_bucket >= lower_bound or domain_bucket < (upper_bound % 100)
            if not in_domain:
                return {"value": flag.default_value, "reason": "excluded_by_conflict_domain"}
        else:
            bucket = cls.get_hash_bucket(f"{exp_seed}_audience", s_id)
            if bucket >= (experiment.audience_share * 100):
                return {"value": flag.default_value, "reason": "not_in_audience_share"}

        if experiment.targeting_rules: 
            from app.utils.dsl_evaluator import DSLEvaluator
            if not DSLEvaluator.evaluate(experiment.targeting_rules, attributes):
                return {"value": flag.default_value, "reason": "targeting_mismatch"}
        
        variant = cls.select_variant(exp_seed, subject_id, experiment.variants)
        if not variant:
            return {"value": flag.default_value, "reason": "variant_not_found"}

        return {
            "value": variant["value"],
            "variant_name": variant["name"],
            "experiment_id": experiment.id,
            "reason": "experiment_match"
        }