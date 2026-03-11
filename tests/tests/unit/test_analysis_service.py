from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from administrador.analytics import service

from core.models import (
    Paciente,
    Atendimento,
    Chamada,
    Guiche,
    CustomUser,
)


class AnalysisServiceTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.user = CustomUser.objects.create(
            username="testuser",
            cpf="90000000010",
            first_name="Test",
            last_name="User",
        )
        self.user.set_password("pass")
        self.user.save()

    def test_total_senhas_generated(self):
        p1 = Paciente.objects.create(senha="A001")
        p2 = Paciente.objects.create(senha="A002")
        # auto_now_add prevents passing value on create, so update explicitly
        Paciente.objects.filter(pk=p1.pk).update(
            horario_geracao_senha=self.now - timedelta(days=1)
        )
        Paciente.objects.filter(pk=p2.pk).update(horario_geracao_senha=self.now)
        start = self.now - timedelta(hours=1)
        end = self.now + timedelta(hours=1)
        self.assertEqual(service.total_senhas_generated(start, end), 1)

    def test_throughput_by_day(self):
        p1 = Paciente.objects.create(senha="X1")
        p2 = Paciente.objects.create(senha="X2")
        p3 = Paciente.objects.create(senha="Y1")
        Paciente.objects.filter(pk=p1.pk).update(
            horario_geracao_senha=self.now - timedelta(days=1)
        )
        Paciente.objects.filter(pk=p2.pk).update(
            horario_geracao_senha=self.now - timedelta(days=1)
        )
        Paciente.objects.filter(pk=p3.pk).update(horario_geracao_senha=self.now)
        start = self.now - timedelta(days=2)
        end = self.now + timedelta(days=1)
        res = list(service.throughput_by_day(start, end))
        days = {r["day"]: r["count"] for r in res}
        self.assertEqual(days.get((self.now - timedelta(days=1)).date()), 2)
        self.assertEqual(days.get(self.now.date()), 1)

    def test_average_wait_time(self):
        p = Paciente.objects.create(senha="W1")
        Paciente.objects.filter(pk=p.pk).update(
            horario_geracao_senha=self.now - timedelta(minutes=30)
        )
        Atendimento.objects.create(paciente=p, funcionario=self.user)
        start = self.now - timedelta(hours=1)
        end = timezone.now() + timedelta(hours=1)
        avg = service.average_wait_time(start, end)
        self.assertIsNotNone(avg)
        # avg is a timedelta; ensure it's approximately 30 minutes
        self.assertGreaterEqual(
            getattr(avg, "total_seconds", lambda: float(avg))(), 29 * 60
        )

    def test_current_queue_length(self):
        Paciente.objects.create(senha="Q1", atendido=False)
        Paciente.objects.create(senha="Q2", atendido=True)
        self.assertEqual(service.current_queue_length(), 1)

    def test_peak_hours(self):
        dt1 = self.now.replace(hour=9, minute=0, second=0, microsecond=0)
        dt2 = self.now.replace(hour=9, minute=30, second=0, microsecond=0)
        dt3 = self.now.replace(hour=15, minute=0, second=0, microsecond=0)
        p1 = Paciente.objects.create(senha="P1")
        p2 = Paciente.objects.create(senha="P2")
        p3 = Paciente.objects.create(senha="P3")
        Paciente.objects.filter(pk=p1.pk).update(horario_geracao_senha=dt1)
        Paciente.objects.filter(pk=p2.pk).update(horario_geracao_senha=dt2)
        Paciente.objects.filter(pk=p3.pk).update(horario_geracao_senha=dt3)
        start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = self.now.replace(hour=23, minute=59, second=59, microsecond=999999)
        res = list(service.peak_hours(start, end))
        raw_hours = {r["hour"]: r["count"] for r in res}

        def count_for(target_hour):
            total = 0
            for k, v in raw_hours.items():
                try:
                    if isinstance(k, int):
                        key = k
                    elif hasattr(k, "hour"):
                        key = int(k.hour)
                    else:
                        key = int(k)
                except Exception:
                    continue
                if key == target_hour:
                    total += int(v)
            return total

        self.assertEqual(count_for(9), 2)
        self.assertEqual(count_for(15), 1)

    def test_guiche_utilization(self):
        Guiche.objects.create(numero=1, em_atendimento=True)
        Guiche.objects.create(numero=2, em_atendimento=False)
        self.assertAlmostEqual(service.guiche_utilization(), 0.5)

    def test_reanuncio_rate(self):
        start = self.now - timedelta(hours=1)
        end = self.now + timedelta(hours=1)
        g = Guiche.objects.create(numero=10)
        p = Paciente.objects.create(senha="R1")
        Chamada.objects.create(paciente=p, guiche=g, acao="chamada")
        Chamada.objects.create(paciente=p, guiche=g, acao="reanuncio")
        Chamada.objects.all().update(data_hora=self.now)
        rate = service.reanuncio_rate(start, end)
        self.assertAlmostEqual(rate, 0.5)

    def test_throughput_date_grouping_edge(self):
        # Ensure grouping is done by the Python date() of datetimes (stable across DB timezone behavior)
        dt1 = self.now.replace(hour=0, minute=30, second=0, microsecond=0)
        dt2 = self.now.replace(hour=23, minute=30, second=0, microsecond=0)
        p1 = Paciente.objects.create(senha="E1")
        p2 = Paciente.objects.create(senha="E2")
        Paciente.objects.filter(pk=p1.pk).update(horario_geracao_senha=dt1)
        Paciente.objects.filter(pk=p2.pk).update(horario_geracao_senha=dt2)
        start = (self.now - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = (self.now + timedelta(days=1)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        res = list(service.throughput_by_day(start, end))
        days = {r["day"]: r["count"] for r in res}
        self.assertEqual(days.get(self.now.date()), 2)
