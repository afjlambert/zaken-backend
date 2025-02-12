from apps.camunda.services import CamundaService
from apps.decisions.models import Decision
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Decision, dispatch_uid="decision_complete_camunda_task")
def update_decision_with_summon(sender, instance, created, **kwargs):
    """
    TODO: Temporary hook to update decision with a summon instance.
    This will be resolved when we support multiple summons.
    """
    if created:
        # TODO: create belastingdienst number
        if instance.case.summons.count() == 1:
            instance.summon = instance.case.summons.all()[0]
            instance.save()

    task = CamundaService().get_task_by_task_name_id_and_camunda_id(
        "task_create_decision", instance.case.camunda_id
    )
    if task:
        CamundaService().complete_task(
            task["id"],
            {"type_besluit": {"value": instance.decision_type.camunda_option}},
        )
