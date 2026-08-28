from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_alter_customuser_sala"),
    ]

    operations = [
        migrations.AddField(
            model_name="chamada",
            name="profissional_saude",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="chamadas_no_guiche",
                to="core.customuser",
                verbose_name="Profissional de Saúde",
            ),
        ),
    ]