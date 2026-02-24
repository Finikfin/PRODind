from sqlalchemy import select, func
from datetime import datetime
from app.database.models import Experiment, Guardrail, ExperimentStatus, Exposure, Conversion, GuardrailAction, ExperimentOutcome

class GuardrailService:
    @staticmethod
    async def check_and_trigger(session, experiment_id):
        res = await session.execute(
            select(Guardrail).where(
                Guardrail.experiment_id == experiment_id,
                Guardrail.is_triggered == False
            )
        )
        guardrails = res.scalars().all()
        if not guardrails:
            return

        exp_count = await session.scalar(
            select(func.count(Exposure.id)).where(Exposure.experiment_id == experiment_id)
        )
        if exp_count == 0: return

        for gr in guardrails:
            conv_count = await session.scalar(
                select(func.count(Conversion.id))
                .join(Exposure, Conversion.decision_id == Exposure.decision_id)
                .where(Exposure.experiment_id == experiment_id)
                .where(Conversion.goal_type == gr.metric_key)
            )

            current_value = conv_count / exp_count
            
            triggered = False
            if gr.operator == ">" and current_value > gr.threshold:
                triggered = True
            elif gr.operator == "<" and current_value < gr.threshold:
                triggered = True

            if triggered:
                gr.is_triggered = True
                gr.triggered_at = datetime.utcnow()
                
                exp_res = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
                exp = exp_res.scalar_one()
                
                if gr.action == GuardrailAction.PAUSE:
                    exp.status = ExperimentStatus.PAUSED
                elif gr.action == GuardrailAction.ROLLBACK:
                    exp.status = ExperimentStatus.FINISHED
                    exp.outcome = ExperimentOutcome.ROLLBACK
                    exp.conclusion = f"Auto-rollback by guardrail: {gr.metric_key}"