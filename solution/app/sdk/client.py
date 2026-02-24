import requests
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

class Decision:
    """Объект решения, который получает программист"""
    def __init__(self, key: str, value: Any, decision_id: str = None, metadata: dict = None):
        self.key = key
        self.value = value
        self.decision_id = decision_id
        self.metadata = metadata or {}

class LottyClient:
    def __init__(self, api_url: str, timeout: float = 1.0):
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout

    def resolve(self, subject_id: UUID, keys: List[str], attributes: dict = None) -> Dict[str, Decision]:
        """Основной метод: возвращает словарь объектов Decision"""
        payload = {
            "subject_id": str(subject_id),
            "keys": keys,
            "attributes": attributes or {}
        }
        try:
            response = requests.post(f"{self.api_url}/decide/", json=payload, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return {
                    item["key"]: Decision(
                        key=item["key"],
                        value=item["value"],
                        decision_id=item["decision_id"],
                        metadata=item.get("metadata", {})
                    ) for item in data["results"]
                }
        except Exception as e:
            print(f"SDK Error: {e}")
        
        return {}

    def track(self, subject_id: UUID, decision_id: str, goal_type: str):
        """Отправка конверсии"""
        payload = {
            "subject_id": str(subject_id),
            "decision_id": decision_id,
            "goal_type": goal_type
        }
        requests.post(f"{self.api_url}/analytics/track", json=payload, timeout=self.timeout)