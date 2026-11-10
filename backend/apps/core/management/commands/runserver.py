from django.contrib.staticfiles.management.commands import runserver as staticfiles_runserver


class Command(staticfiles_runserver.Command):
    """`runserver` that does not require a live database at boot.

    The stock command opens a connection to read ``django_migrations``. This
    project's schema is owned by ``db/schema.sql`` and every model is
    ``managed = False``, so there are never migrations to apply and the check
    only prevents the server from starting when MySQL is stopped.
    """

    def check_migrations(self, *args, **kwargs):
        return
