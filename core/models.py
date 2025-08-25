from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import datetime
from django.conf import settings


class CustomUser(AbstractUser):
    FUNCAO_CHOICES = (
        ('administrador', 'Administrador'),
        ('recepcionista', 'Recepcionista'),
        ('guiche', 'Guichê'),
        ('profissional_saude', 'Profissional de Saúde'),
    )
    funcao = models.CharField(max_length=20, choices=FUNCAO_CHOICES, default='recepcionista', verbose_name="Função")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    # Outros campos específicos do funcionário
    data_admissao = models.DateField(null=True, blank=True, verbose_name="Data de Admissão")
    funcao = models.CharField(max_length=20, choices=FUNCAO_CHOICES, default='recepcionista', verbose_name="Função") # coloquei agora
    sala = models.IntegerField(null=True, blank=True, verbose_name="Sala do Profissional") # coloquei agora

    USERNAME_FIELD = 'cpf'  # Use o CPF como o campo de nome de usuário
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username' ]  # Campos obrigatórios,

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Paciente(models.Model):
    SENHA_CHOICES = [
        ('E', 'Exames'),
        ('C', 'Curativos'),
        ('P', 'Psicologia'),
        ('G', 'Geral'),
        ('D', 'Dentista'),
        ('A', 'Primeiro Atendimento'),
        ('NH', 'Hansenologia'),
        ('H', 'Hansenologia Retorno'),
        ('U', 'Ultrassom'),
    ]
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo",  null=True, blank=True)
    tipo_senha = models.CharField(
        max_length=2,
        choices=SENHA_CHOICES,
        verbose_name="Tipo de Senha",
        blank=True,
        null=True
    )
    senha = models.CharField(max_length=6, verbose_name="Senha",  null=True, blank=True)
    cartao_sus = models.CharField(max_length=20, verbose_name="Cartão do SUS", blank=True, null=True)
    horario_geracao_senha = models.DateTimeField(auto_now_add=True, verbose_name="Horário da Geração da Senha", blank=True, null=True)
    horario_agendamento = models.DateTimeField(verbose_name="Horário do Agendamento", blank=True, null=True)
    profissional_saude = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Funcionário")
    observacoes = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observações")
    atendido = models.BooleanField(default=False, verbose_name="Atendido")

    def __str__(self):
        return f"{self.nome_completo} (Senha: {self.senha}, Agendamento: {self.horario_agendamento})"

class Atendimento(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, verbose_name="Paciente")
    funcionario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Funcionário")  # Quem realizou o atendimento
    data_hora = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora")
    # Outros campos do atendimento (observações, etc.)

    def __str__(self):
        return f"Atendimento de {self.paciente.nome} por {self.funcionario.username} em {self.data_hora}"

class RegistroDeAcesso(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Usuário")
    data_hora = models.DateTimeField(default=timezone.now, verbose_name="Data e Hora")
    tipo_de_acesso = models.CharField(max_length=10, choices=(('login', 'Login'), ('logout', 'Logout')), verbose_name="Tipo de Acesso")
    endereco_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Endereço IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    view_name = models.CharField(max_length=255, verbose_name="Nome da View", null=True, blank=True)  # Nome da view acessada

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo_de_acesso} - {self.data_hora}"
    
class Guiche(models.Model):
    numero = models.IntegerField(unique=True, verbose_name="Número do Guichê")
    funcionario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Funcionário", related_name='guiches') #Adicionado related_name
    senha_atendida = models.ForeignKey(Paciente, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Senha Atendida")
    em_atendimento = models.BooleanField(default=False, verbose_name="Em Atendimento")
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário",related_name='guiche')

    def __str__(self):
        return f"Guichê {self.numero} - {self.funcionario.first_name if self.funcionario else 'Livre'}"
    
class Chamada(models.Model):
    ACOES = (
        ('chamada', 'Chamada'),
        ('reanuncio', 'Reanúncio'),
        ('confirmado', 'Confirmado'),
    )
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, verbose_name="Paciente")
    guiche = models.ForeignKey(Guiche, on_delete=models.CASCADE, verbose_name="Guichê")
    acao = models.CharField(max_length=15, choices=ACOES)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.get_acao_display()} - {self.paciente.senha} no Guichê {self.guiche.numero}"
    

#class ProfissionalDeSaude(models.Model):
    #sala = models.IntegerField(unique=True, verbose_name="Sala do Profissional")
    #funcionario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Funcionário", related_name='profissional_saude')
    #senha_atendida = models.ForeignKey(Paciente, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Senha Atendida")
    #em_consulta = models.BooleanField(default=False, verbose_name="Em Consulta")
    #user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário",related_name='profissiomal_saude')

    #def __str__(self):
        #return f"ProfissionalDeSaude {self.sala} - {self.funcionario.first_name if self.funcionario else 'Livre'}"
    

class ChamadaProfissional(models.Model):
    ACOES = (
        ('chamada', 'Chamada'),
        ('reanuncio', 'Reanúncio'),
        ('confirmado', 'Confirmado'),
        ('encaminha', 'Encaminha')
    )
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, verbose_name="Paciente")
    profissional_saude = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="ProfissionalDeSaude")
    acao = models.CharField(max_length=15, choices=ACOES)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.get_acao_display()} - {self.paciente.senha} no ProfissionalDeSaude {self.profissional_saude.first_name}"