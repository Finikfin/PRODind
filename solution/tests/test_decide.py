import uuid
from app.services.decision_engine import DecisionEngine
from app.database.models import Experiment, ExperimentStatus

async def create_exp(session, flag, variants, share=1.0):
    exp = Experiment(
        flag_id=flag.id,
        name="exp",
        status=ExperimentStatus.RUNNING,
        audience_share=share,
        variants=variants
    )
    session.add(exp)
    await session.commit()
    return exp

async def test_same_user_same_variant(session, flag):
    variants = [
        {"name": "A", "weight": 50, "value": 0},
        {"name": "B", "weight": 50, "value": 1},
    ]
    exp = await create_exp(session, flag, variants)

    uid = uuid.uuid4()
    d1 = await DecisionEngine.decide(flag, exp, uid, {})
    d2 = await DecisionEngine.decide(flag, exp, uid, {})

    assert d1["variant_name"] == d2["variant_name"]

async def test_audience_exclusion_returns_default(session, flag):
    variants = [{"name": "A", "weight": 100, "value": 1}]
    exp = await create_exp(session, flag, variants, share=0.0)

    uid = uuid.uuid4()
    d = await DecisionEngine.decide(flag, exp, uid, {})

    assert d["value"] == flag.default_value
    assert d["reason"] == "not_in_audience_share"