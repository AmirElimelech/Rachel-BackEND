from django.apps import AppConfig


class RachelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Rachel'



    def ready(self):
        import Rachel.signals


