from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_chamada_profissional_saude"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="prioridade",
            field=models.CharField(
                choices=[
                    ("normal", "Normal"),
                    ("prioritario", "Prioritário"),
                    ("super_prioritario", "Super prioritário"),
                ],
                default="normal",
                max_length=20,
                verbose_name="Prioridade",
            ),
        ),
        migrations.AddField(
            model_name="chamada",
            name="prioridade",
            field=models.CharField(
                blank=True,
                choices=[
                    ("normal", "Normal"),
                    ("prioritario", "Prioritário"),
                    ("super_prioritario", "Super prioritário"),
                ],
                max_length=20,
                null=True,
                verbose_name="Prioridade no momento da chamada",
            ),
        ),
    ]