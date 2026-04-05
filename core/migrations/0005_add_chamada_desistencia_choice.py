"""Empty migration to record addition of 'desistencia' choice to Chamada.ACOES.

This change only adds a new choice in the Python model and does not
require database schema changes. The empty migration ensures the
project's migration history reflects the code change.

Generated manually.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_customuser_failed_login_attempts_and_more"),
    ]

    operations = []
