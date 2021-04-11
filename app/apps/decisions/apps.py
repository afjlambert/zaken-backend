from django.apps import AppConfig


class DecisionsConfig(AppConfig):
    name = "apps.decisions"

    def ready(self):
        import apps.decisions.signals  # noqa
