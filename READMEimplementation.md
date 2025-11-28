# Implementação em Produção - SGA LSL Univesp

## Pré-requisitos
- Servidor Linux com Docker e Docker Compose instalados
- PostgreSQL (via Docker)
- Porta 80 disponível para Nginx

## Passo a Passo

### 1. Clonagem e Configuração Inicial

- Adicione os arquivos do sistema no diretório do servidor (Por ex. /home/user/python-sga-lsl-univesp)
- Entre no diretório (cd /caminho/do/sistema)

```bash
# No diretório do projeto (onde está entrypoint.sh)
chmod +x entrypoint.sh
```

### 2. Configuração do Ambiente (.env)
Edite o arquivo `.env` com valores seguros para produção:

```env
POSTGRES_USER=sga_prod_user
POSTGRES_PASSWORD=SuaSenhaSuperSeguraAqui123!
POSTGRES_DB=sga_prod_db
SECRET_KEY=SuaSecretKeySuperSeguraDePeloMenos50CaracteresAqui
DEBUG=0
DATABASE_URL=postgres://sga_prod_user:SuaSenhaSuperSeguraAqui123!@db:5432/sga_prod_db

# Superuser para produção
DJANGO_SUPERUSER_USERNAME=admin_cpf  # CPF válido sem máscara
DJANGO_SUPERUSER_EMAIL=admin@seudominio.com
DJANGO_SUPERUSER_PASSWORD=SenhaSuperSeguraParaAdmin
```

**Recomendações de Segurança:**
- Use senhas fortes e únicas (mínimo 16 caracteres, com letras, números e símbolos)
- Mantenha o `DEBUG=0` em produção
- Use um `SECRET_KEY` gerado aleatoriamente (pode usar `openssl rand -hex 32`)
- Restrinja acesso ao arquivo `.env` (chmod 600)
- Considere usar variáveis de ambiente do sistema em vez de arquivo `.env` para maior segurança

### 3. Build e Inicialização
```bash
# Build das imagens
docker-compose -f docker-compose.prod.yml build

# Inicialização (cria banco, superuser, guichês)
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Verificação
Acesse `http://seu-servidor` e faça login com o superuser configurado.

Sugestão de fluxo inicial após o primeiro login:

- **Login do administrador:** faça login usando as credenciais do superuser definidas no arquivo `.env` (campo `DJANGO_SUPERUSER_USERNAME` e `DJANGO_SUPERUSER_PASSWORD`).
- **Ajuste do perfil:** após o login, acesse a interface de administrador e edite suas próprias informações de contato/perfil para que constem corretamente no sistema.
- **Cadastrar funcionários:** comece a adicionar os funcionários no sistema pela interface de administração. Recomendamos chamar cada funcionário até o computador do administrador para que o próprio funcionário preencha ou confirme seus dados na tela — a interface é responsiva e também pode ser usada a partir de um smartphone caso prefira levar o dispositivo até o funcionário.
- **Informar acesso aos funcionários:** depois de criar a conta, informe ao funcionário a URL que ele deve digitar no navegador para acessar o sistema (ex.: `http://seu-servidor/` ou `http://seu-servidor/login`).

- **IMPORTANTE:** Esses passos garantem que o cadastro seja feito com supervisão e que cada funcionário saiba imediatamente como acessar a aplicação.

- **Preparar as tvs:** Cada tv tem uma url especifica (`http://seu-servidor/guiche/tv1` e `http://seu-servidor/profissional_saude/tv2`).
Instale os cabos hdmi em quaisquer computadores proximos (maximo 10m de distancia) ou alguma outra solução para que as tvs tenham acesso remoto a algum computador para exibirem a interface web (É possivel testar o navegador da própria TV caso seja Smart).
Esses endpoints nao precisam de login.

### 5. Configuração para Iniciar Automaticamente no Boot

#### Opção 1: Usando systemd (Recomendado)
Crie um serviço systemd:

```bash
sudo nano /etc/systemd/system/sga.service
```

Conteúdo do arquivo:
```ini
[Unit]
Description=SGA LSL Univesp
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/caminho/para/python-sga-LSL-Univesp
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Habilite e inicie:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sga.service
sudo systemctl start sga.service
```

#### Opção 2: Usando cron (@reboot)
Adicione ao crontab do root:
```bash
sudo crontab -e
```

Adicione a linha:
```cron
@reboot cd /caminho/para/python-sga-LSL-Univesp && /usr/bin/docker-compose -f docker-compose.prod.yml up -d
```

### 6. Manutenção
- **Logs:** `docker-compose -f docker-compose.prod.yml logs -f`
- **Backup do banco:** Use volumes Docker ou scripts externos
- **Atualizações:** Pare o serviço, atualize o código, rebuild e reinicie

### 7. Segurança Adicional

#### Firewall e Restrição de Acesso
Para garantir que apenas dispositivos autorizados (ex.: rede do hospital) acessem a aplicação, configure restrições por IP no Nginx e no firewall do servidor.

##### Opção 1: Restrição no Nginx (Recomendado para Controle Fino)
Edite o arquivo `nginx.conf` e adicione as linhas `allow` e `deny` no bloco `server`:

```nginx
server {
    listen 80;
    server_name localhost;

    # Restringir acesso por IP (ajuste a sub-rede do hospital)
    allow 192.168.1.0/24;  # Permite sub-rede específica (ex.: rede interna do hospital)
    deny all;  # Bloqueia todos os outros IPs

    location / {
        proxy_pass http://django;
        # ... resto da configuração
    }
    # ... outras locations
}
```

- Substitua `192.168.1.0/24` pela sub-rede real da rede do hospital (ex.: `10.0.0.0/8` para redes privadas).
- Após editar, reinicie o Nginx: `docker-compose -f docker-compose.prod.yml restart nginx`.

##### Opção 2: Firewall no Servidor (ufw - Ubuntu/Debian)
Use `ufw` para restringir acesso na porta do Nginx (padrão 80, ou mude para outra como 8080 no `docker-compose.prod.yml`).

Instale e configure o ufw (se não estiver instalado):
```bash
sudo apt update
sudo apt install ufw
sudo ufw enable
```

Permita apenas a sub-rede específica:
```bash
sudo ufw allow from 192.168.1.0/24 to any port 80  # Permite sub-rede na porta 80
sudo ufw deny 80  # Bloqueia todos os outros na porta 80
```

- Ajuste a sub-rede e porta conforme necessário.
- Verifique o status: `sudo ufw status`.
- Isso adiciona uma camada extra de segurança além do Nginx.

#### Outras Medidas de Segurança
- **HTTPS**: Configure SSL no Nginx para criptografar o tráfego (use Let's Encrypt ou certificado próprio).
- **Monitoramento**: Monitore logs do Nginx e Docker regularmente: `docker-compose -f docker-compose.prod.yml logs -f nginx`.
- **Atualizações**: Mantenha Docker, Nginx, Django e dependências atualizadas para patches de segurança.
- **Backup**: Faça backups regulares do banco de dados (use volumes Docker ou ferramentas como `pg_dump`).

### 8. HTTPS / Certificados (Passo-a-passo)

Para produção recomendamos usar HTTPS para criptografar o tráfego mesmo em redes internas. Abaixo estão 3 opções com passos concretos.

Opção A — Self-signed (rápido, gera aviso no navegador)

1. Gere certificados no servidor (ex.: dentro do diretório `nginx/ssl` no repo):

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout nginx/ssl/nginx.key \
    -out nginx/ssl/nginx.crt \
    -subj "/CN=sga.hospital.local"
```

2. Monte os arquivos no serviço `nginx` do `docker-compose.prod.yml` (exemplo):

```yaml
services:
    nginx:
        volumes:
            - ./nginx.conf:/etc/nginx/nginx.conf:ro
            - ./nginx/ssl:/etc/nginx/ssl:ro
            - staticfiles:/app/staticfiles
        ports:
            - "443:443"
            - "80:80"
```

3. Adicione um bloco `server` em `nginx.conf` para TLS (exemplo):

```nginx
server {
        listen 443 ssl;
        server_name sga.hospital.local;

        ssl_certificate /etc/nginx/ssl/nginx.crt;
        ssl_certificate_key /etc/nginx/ssl/nginx.key;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
                proxy_pass http://django;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ { alias /app/staticfiles/; }
        location /media/ { alias /app/media/; }
}

server {
        listen 80;
        server_name sga.hospital.local;
        return 301 https://$host$request_uri;
}
```

4. Reinicie o nginx container:

```bash
docker-compose -f docker-compose.prod.yml up -d --no-deps --build nginx
# ou
docker-compose -f docker-compose.prod.yml restart nginx
```

Nota: navegadores mostrarão aviso de certificado não confiável. Use apenas para testes ou quando for aceitável confiar manualmente.

Opção B — mkcert (boa para LAN gerenciada)

- `mkcert` cria um CA local e pode gerar certificados confiáveis se você instalar a CA em todas as máquinas clientes (TI do hospital pode distribuir a CA via políticas):

1. Instale `mkcert` (veja docs: https://github.com/FiloSottile/mkcert).
2. No host de administração gere os certificados:

```bash
mkcert -install
mkcert sga.hospital.local 192.168.1.10
# Isso gera algo como sga.hospital.local+IP.pem e key file
```

3. Monte as chaves em `nginx` como no passo A e reinicie. Instale a CA raiz `mkcert` nos navegadores/hosts clientes (TI).

Opção C — Let's Encrypt (melhor se tiver domínio público)

1. Se seu servidor tem um domínio público válido (`sga.hospital.example`) e aponta para o IP, use `certbot`:

```bash
sudo apt update
sudo apt install certbot
sudo certbot certonly --standalone -d sga.hospital.example
```

2. Monte `/etc/letsencrypt/live/sga.hospital.example/fullchain.pem` e `privkey.pem` no container `nginx` (somente se terminar TLS no container). Use `certbot renew` em cron/systemd timer.

Firewall e HSTS
- Após habilitar HTTPS, ajuste o `ufw` para permitir apenas a sub-rede hospitalar nas portas 443/80:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 443
sudo ufw deny 443
```

- Cuidado com HSTS: só ative `add_header Strict-Transport-Security` quando tiver certificados confiáveis e controle sobre os clientes (HSTS impede acesso HTTP por período configurado).

### 9. Desinstalação completa

- Caso tenha interesse em desinstalar completamente o sistema rode o comando

```bash
docker-compose -f docker-compose.prod.yml down -v
```
(Use com cuidado, remove também todos os dados do Banco de dados)

---
