import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sga.settings_test')
import django
django.setup()

from core.forms import CadastrarPacienteForm
data = {
    'nome_completo': 'Teste',
    'cartao_sus': '999999999999999',  # Cartão que não existe
    'telefone_celular': '11 99999 9999',
    'tipo_senha': 'G'
}
form = CadastrarPacienteForm(data=data)
print('Form is valid:', form.is_valid())
if not form.is_valid():
    print('Errors:', form.errors)
else:
    print('Telefone limpo:', form.cleaned_data.get('telefone_celular'))