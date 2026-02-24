import uuid
from datetime import datetime
from app.database.models import Exposure, Conversion

async def test_conversion_requires_exposure(session):
    conv = Conversion(
        event_id="e1",
        subject_id=uuid.uuid4(),
        goal_type="purchase",
        decision_id="missing"
    )
    session.add(conv)
    try:
        await session.commit()
        ok = True
    except:
        ok = False

    assert not ok

async def test_duplicate_event_dedup(session):
    uid = uuid.uuid4()
    exp_id = uuid.uuid4()

    exposure = Exposure(
        experiment_id=exp_id,
        subject_id=uid,
        variant_name="A",
        decision_id="d1"
    )
    session.add(exposure)
    await session.commit()

    c1 = Conversion(event_id="e1", subject_id=uid, goal_type="x", decision_id="d1")
    c2 = Conversion(event_id="e1", subject_id=uid, goal_type="x", decision_id="d1")

    session.add_all([c1, c2])
    await session.commit()

    rows = (await session.execute("select count(*) from conversions")).scalar()
    assert rows == 1