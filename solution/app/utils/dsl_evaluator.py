import operator
from typing import Any, Dict, List, Union

class DSLEvaluator:
    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "in": lambda a, b: a in b if isinstance(b, list) else False,
        "not_in": lambda a, b: a not in b if isinstance(b, list) else True,
    }

    @classmethod
    def evaluate(cls, rules: Dict[str, Any], attributes: Dict[str, Any]) -> bool:
        if not rules:
            return True

        if "AND" in rules:
            return all(cls.evaluate(r, attributes) for r in rules["AND"])
        if "OR" in rules:
            return any(cls.evaluate(r, attributes) for r in rules["OR"])
        if "NOT" in rules:
            return not cls.evaluate(rules["NOT"], attributes)

        field = rules.get("field")
        op_str = rules.get("op")
        expected_value = rules.get("value")

        if field not in attributes:
            return False

        actual_value = attributes[field]
        op_func = cls.OPERATORS.get(op_str)

        if not op_func:
            return False

        try:
            return op_func(actual_value, expected_value)
        except Exception:
            return False