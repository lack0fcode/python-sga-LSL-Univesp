from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime, time
import random
import secrets
import logging

from core.models import Paciente, Atendimento, Guiche, Chamada, CustomUser


class Command(BaseCommand):
    help = "Popula o banco com dados de exemplo para KPIs (últimos N dias)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=14, help="Número de dias para popular"
        )
        parser.add_argument(
            "--per-day",
            type=int,
            default=60,
            help="Média de senhas geradas por dia",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Seed para RNG (reprodutibilidade)",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            default=False,
            help="Trunca tabelas antes de popular",
        )
        parser.add_argument(
            "--walkin",
            type=float,
            default=0.6,
            help="Fração de pacientes walk-in (0-1)",
        )
        parser.add_argument(
            "--long-wait",
            type=float,
            default=0.15,
            help="Probabilidade de espera longa (0-1)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        per_day = options["per_day"]
        seed = options.get("seed")
        if seed is not None:
            # seeding here is for reproducible synthetic data only
            random.seed(seed)  # nosec B311

        logger = logging.getLogger(__name__)

        now = timezone.now()
        # include today when user requests N days: make the range inclusive
        # e.g. days=14 -> generate on the last 14 days including today
        start_day = (now - timedelta(days=max(1, days - 1))).date()

        # optionally truncate tables to start fresh
        if options.get("truncate"):
            self.stdout.write(
                "Truncando tabelas Paciente, Atendimento, Chamada, Guiche..."
            )
            Atendimento.objects.all().delete()
            Chamada.objects.all().delete()
            Paciente.objects.all().delete()
            Guiche.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Truncado."))

        # Ensure there are some guichês
        guiches = list(Guiche.objects.all())
        if not guiches:
            # create 4 guichês
            for i in range(1, 5):
                Guiche.objects.create(numero=i)
            guiches = list(Guiche.objects.all())

        # pick some funcionarios (if available), else fallback to any user
        funcionarios = list(CustomUser.objects.all()) or []

        created = 0
        atendidos = 0

        # precompute hour weights for realistic morning/afternoon peaks
        # expand business hours slightly to spread timestamps
        hours = list(range(6, 22))  # 6..21
        hour_weights = []
        for h in hours:
            # base weight
            w = 1.0
            # morning peak 9-11
            if 9 <= h <= 11:
                w += 3.0
            # lunch dip 12
            if h == 12:
                w -= 0.5
            # afternoon peak 14-16
            if 14 <= h <= 16:
                w += 2.0
            hour_weights.append(max(0.05, w))

        for day_offset in range(days):
            d = start_day + timedelta(days=day_offset)
            # vary per day (mild variation) and ensure at least 0
            today_count = max(0, int(random.gauss(per_day, per_day * 0.20)))

            for i in range(today_count):
                # pick hour according to weighted peaks, add jitter
                hour = random.choices(hours, weights=hour_weights, k=1)[0]
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                gen_dt = datetime.combine(
                    d, time(hour=hour, minute=minute, second=second)
                )
                gen_dt = timezone.make_aware(gen_dt, timezone.get_current_timezone())

                senha = f"{random.randint(1, 999):03d}"  # nosec B311
                paciente = Paciente.objects.create(
                    nome_completo=f"Paciente {created+1}",
                    senha=senha,
                    atendido=False,
                )
                # horario_geracao_senha uses auto_now_add on the model; set it via update()
                Paciente.objects.filter(pk=paciente.pk).update(
                    horario_geracao_senha=gen_dt
                )
                created += 1

                # decide if will be attended; walk-ins have slightly lower immediate attend rate
                walkin_prop = float(options.get("walkin", 0.6))
                attend_prob = 0.85 if random.random() > walkin_prop else 0.6
                will_be_attended = random.random() < attend_prob
                if will_be_attended:
                    # determine if this will be a long wait based on parameter
                    if random.random() < options.get("long_wait", 0.15):
                        # long tail waits
                        wait_minutes = max(5, int(random.gauss(60, 40)))
                    else:
                        # typical waits
                        wait_minutes = max(1, int(random.gauss(12, 10)))

                    attend_dt = gen_dt + timedelta(minutes=wait_minutes)

                    # pick funcionario
                    if funcionarios:
                        func = random.choice(funcionarios)
                    else:
                        func = None

                    # To create Atendimento we need a funcionario; if none exists, create a dummy
                    if func is None:
                        # create a dummy user with a secure random password for tests
                        pwd = secrets.token_urlsafe(12)
                        func = CustomUser.objects.create_user(
                            username=f"auto_user_{random.randint(1000, 9999)}",  # nosec B311
                            cpf=f"00000000000{random.randint(10, 99)}",  # nosec B311
                            password=pwd,
                            first_name="Auto",
                            last_name="User",
                        )
                        logger.debug("Created auto user %s", func.username)

                    at = Atendimento.objects.create(
                        paciente=paciente,
                        funcionario=func,
                    )
                    # data_hora uses auto_now_add; set the intended timestamp via update()
                    Atendimento.objects.filter(pk=at.pk).update(data_hora=attend_dt)
                    paciente.atendido = True
                    paciente.save(update_fields=["atendido"])
                    atendidos += 1

                    # create one chamada slightly before atendimento
                    rand_minutes = random.randint(0, 10)  # nosec B311
                    call_dt = attend_dt - timedelta(minutes=rand_minutes)
                    guiche = random.choice(guiches)
                    ch = Chamada.objects.create(
                        paciente=paciente,
                        guiche=guiche,
                        acao="chamada",
                    )
                    Chamada.objects.filter(pk=ch.pk).update(data_hora=call_dt)

                    # sometimes reanuncio
                    if random.random() < 0.05:
                        reanuncio_dt = call_dt + timedelta(minutes=random.randint(1, 5))
                        ch2 = Chamada.objects.create(
                            paciente=paciente,
                            guiche=guiche,
                            acao="reanuncio",
                        )
                        Chamada.objects.filter(pk=ch2.pk).update(data_hora=reanuncio_dt)

        self.stdout.write(
            self.style.SUCCESS(f"Criados {created} pacientes ({atendidos} atendidos)")
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Pronto. Rodar novamente com --days/--per-day para ajustar."
            )
        )
