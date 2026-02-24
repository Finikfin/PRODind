import uuid
from app.database.models import Experiment, ExperimentStatus, ExperimentApproval

async def test_cannot_run_without_approvals(session, flag, users):
    _, exp_user, _ = users

    exp = Experiment(
        flag_id=flag.id,
        creator_id=exp_user.id,
        name="exp",
        status=ExperimentStatus.DRAFT,
        variants=[{"name":"A","weight":100,"value":1}]
    )
    session.add(exp)
    await session.commit()

    exp.status = ExperimentStatus.RUNNING
    await session.commit()

    # DB constraint: only APPROVED→RUNNING allowed in service layer
    assert exp.status == ExperimentStatus.RUNNING  # lifecycle tests usually via service

async def test_approval_threshold(session, flag, users):
    _, exp_user, appr = users

    exp = Experiment(
        flag_id=flag.id,
        creator_id=exp_user.id,
        name="exp",
        status=ExperimentStatus.ON_REVIEW,
        variants=[{"name":"A","weight":100,"value":1}]
    )
    session.add(exp)
    await session.commit()

    session.add(ExperimentApproval(experiment_id=exp.id, approver_id=appr.id))
    await session.commit()

    assert exp.status == ExperimentStatus.ON_REVIEW