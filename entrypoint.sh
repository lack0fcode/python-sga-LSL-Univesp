#!/bin/sh
set -e

echo "Entrypoint: aguardando banco de dados..."

# Simple wait-for-postgres loop using psql (if available) or python fallback
if command -v pg_isready >/dev/null 2>&1; then
  until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${POSTGRES_USER:-postgres}"; do
    echo "Aguardando Postgres..."
    sleep 1
  done
else
  python - <<PY
import os, time
from urllib.parse import urlparse
import psycopg2
url=os.environ.get('DATABASE_URL')
if not url:
    print('DATABASE_URL não definido')
    raise SystemExit(1)
res=urlparse(url)
host=res.hostname or os.environ.get('DB_HOST','db')
port=res.port or int(os.environ.get('DB_PORT',5432))
user=res.username or os.environ.get('POSTGRES_USER')
password=res.password or os.environ.get('POSTGRES_PASSWORD')
dbname=res.path.lstrip('/') or os.environ.get('POSTGRES_DB')
for _ in range(60):
    try:
        conn=psycopg2.connect(host=host,port=port,user=user,password=password,dbname=dbname)
        conn.close()
        print('Banco disponível')
        break
    except Exception:
        print('Aguardando Postgres...')
        time.sleep(1)
else:
    print('Timeout esperando pelo banco')
    raise SystemExit(2)
PY

fi

echo "Rodando migrations..."
python manage.py migrate --noinput

echo "Criando superuser se variáveis definidas..."
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python -c "
import os
import django
from django.conf import settings
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sga.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username=os.environ['DJANGO_SUPERUSER_USERNAME']).exists():
    User.objects.create_superuser(
        username=os.environ['DJANGO_SUPERUSER_USERNAME'],
        email=os.environ['DJANGO_SUPERUSER_EMAIL'],
        password=os.environ['DJANGO_SUPERUSER_PASSWORD'],
        first_name='Admin',
        last_name='Sistema',
        cpf=os.environ['DJANGO_SUPERUSER_USERNAME'],
        funcao='administrador'
    )
    print('Superuser criado.')
else:
    user = User.objects.get(username=os.environ['DJANGO_SUPERUSER_USERNAME'])
    if not user.cpf:
        user.cpf = os.environ['DJANGO_SUPERUSER_USERNAME']
        user.save()
        print('Superuser cpf atualizado.')
    if user.funcao != 'administrador':
        user.funcao = 'administrador'
        user.save()
        print('Superuser funcao atualizada para administrador.')
    else:
        print('Superuser já existe.')
"
fi

echo "Criando guiches se não existirem..."
python -c "
import os
import django
from django.conf import settings
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sga.settings')
django.setup()

from core.models import Guiche

for i in range(1, 6):
    if not Guiche.objects.filter(numero=i).exists():
        Guiche.objects.create(numero=i)
        print(f'Guiche {i} criado.')
    else:
        print(f'Guiche {i} já existe.')

# Liberar todos os guichês ao iniciar (para casos de restart sem logout)
Guiche.objects.filter(funcionario__isnull=False).update(funcionario=None)
print('Todos os guichês liberados.')
"

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "Iniciando servidor..."
if [ "$DJANGO_ENV" = "production" ]; then
    echo "Modo produção: usando Gunicorn"
    exec gunicorn sga.wsgi:application --bind 0.0.0.0:8000 --workers 3
else
    echo "Modo desenvolvimento: usando runserver"
    exec python manage.py runserver 0.0.0.0:8000
fi
