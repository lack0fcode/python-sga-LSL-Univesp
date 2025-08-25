from core.models import Paciente
def get_senha_choices():
    return Paciente.SENHA_CHOICES