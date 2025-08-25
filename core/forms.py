# core/forms.py
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Paciente # Importação única


LETRAS_SENHA = [
    ('E', 'Exames'),
    ('C', 'Curativos'),
    ('P', 'Psicologia'),
    ('G', 'Geral'),
    ('D', 'Dentista'),
    ('A', 'Primeiro Atendimento'),
    ('NH', 'Hansenologia'),
    ('H', 'Hansenologia Retorno'),
    ('U', 'Ultrassom')
]

class CadastrarPacienteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        profissionais_de_saude = kwargs.pop('profissionais_de_saude', None)
        super().__init__(*args, **kwargs)
        if profissionais_de_saude:
            self.fields['profissional_saude'].queryset = profissionais_de_saude

    profissional_saude = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(funcao='profissional_saude'),
        label="Profissional de Saúde",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tipo_senha = forms.ChoiceField(
        choices=LETRAS_SENHA,
        label="Tipo de Senha",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Paciente
        fields = [
            'nome_completo',
            'cartao_sus',
            'horario_agendamento',
            'profissional_saude',
            'observacoes',
            'tipo_senha'  # <-- adicionado aqui também
        ]
        widgets = {
            'horario_agendamento': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class CadastrarFuncionarioForm(UserCreationForm):
    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        help_text="Obrigatório. 14 caracteres."
    )
    funcao = forms.ChoiceField(choices=CustomUser.FUNCAO_CHOICES, help_text="Selecione a função do funcionário.")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('cpf', 'username', 'first_name', 'last_name', 'email', 'funcao')
        help_texts = {
            'username': None,
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['cpf']  # Define o username como o CPF
        if commit:
            user.save()
        return user
    
class LoginForm(forms.Form):
    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        widget=forms.TextInput(attrs={'placeholder': 'Digite seu CPF'})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'placeholder': 'Digite sua senha'})
    )


    def clean(self):
        cleaned_data = super().clean()
        cpf = cleaned_data.get('cpf')
        password = cleaned_data.get('password')

        if cpf and password:
            user = authenticate(username=cpf, password=password)  # Use 'cpf' como username
            if user is not None:
                if user.is_active:
                    cleaned_data['user'] = user
                else:
                    raise ValidationError("Esta conta está inativa.")  # Usuário inativo
            else:
                raise ValidationError("CPF ou senha incorretos.")  # Credenciais incorretas

        return cleaned_data