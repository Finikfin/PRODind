import uuid
from datetime import datetime
from app.database.models import Experiment, ExperimentStatus, Guardrail, Exposure, Conversion, GuardrailAction
from app.services.guardrail_service import GuardrailService

async def test_guardrail_pause(session, flag, users):
    _, exp_user, _ = users

    exp = Experiment(
        flag_id=flag.id,
        creator_id=exp_user.id,
        name="exp",
        status=ExperimentStatus.RUNNING,
        started_at=datetime.utcnow(),
        variants=[{"name":"A","weight":100,"value":1}]
    )
    session.add(exp)
    await session.commit()

    gr = Guardrail(
        experiment_id=exp.id,
        metric_key="purchase",
        threshold=0.5,
        operator="<",
        action=GuardrailAction.PAUSE
    )
    session.add(gr)
    await session.commit()

    for i in range(10):
        e = Exposure(
            experiment_id=exp.id,
            subject_id=uuid.uuid4(),
            variant_name="A",
            decision_id=f"d{i}"
        )
        session.add(e)
    await session.commit()

    await GuardrailService.check_and_trigger(session, exp.id)
    await session.refresh(exp)

    assert exp.status == ExperimentStatus.PAUSED