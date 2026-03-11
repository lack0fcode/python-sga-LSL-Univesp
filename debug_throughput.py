import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sga.tests.settings_test")
import django

django.setup()

from core.models import Paciente
from administrador.analytics import service

now = timezone.now()
# create patients
p1 = Paciente.objects.create(senha="X1")
p2 = Paciente.objects.create(senha="X2")
p3 = Paciente.objects.create(senha="Y1")
Paciente.objects.filter(pk=p1.pk).update(horario_geracao_senha=now - timedelta(days=1))
Paciente.objects.filter(pk=p2.pk).update(horario_geracao_senha=now - timedelta(days=1))
Paciente.objects.filter(pk=p3.pk).update(horario_geracao_senha=now)
start = now - timedelta(days=2)
end = now + timedelta(days=1)
res = list(service.throughput_by_day(start, end))
print("throughput res:", res)
print("days mapping:")
for r in res:
    print(r["day"], type(r["day"]), r["count"])
