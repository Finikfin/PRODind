import uuid
from app.database.models import Exposure, Conversion
from app.services.stats_service import StatsService

async def test_stats_per_variant(session):
    exp_id = uuid.uuid4()

    users = [uuid.uuid4() for _ in range(10)]
    for u in users[:5]:
        session.add(Exposure(experiment_id=exp_id, subject_id=u, variant_name="A", decision_id=str(u)))
    for u in users[5:]:
        session.add(Exposure(experiment_id=exp_id, subject_id=u, variant_name="B", decision_id=str(u)))
    await session.commit()

    for u in users[:2]:
        session.add(Conversion(event_id=str(u), subject_id=u, goal_type="purchase", decision_id=str(u)))
    await session.commit()

    stats = await StatsService.get_experiment_stats(session, exp_id, "purchase")

    a = next(x for x in stats if x["variant"]=="A")
    assert a["total_users"] == 5
    assert a["conversions"] == 2