from django.apps import AppConfig


class TrackerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tracker"

    def ready(self):
        import os
        from django.contrib.auth.models import User
        from django.db.utils import OperationalError, ProgrammingError

        # Read environment variables
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")

        if username and password:
            try:
                # Check if superuser exists, if not, create it
                if not User.objects.filter(username=username).exists():
                    User.objects.create_superuser(username, email, password)
                    print(f"Auto-created superuser: {username}")
            except (OperationalError, ProgrammingError):
                # This handles cases where database tables do not exist yet (e.g. before initial migration)
                pass
