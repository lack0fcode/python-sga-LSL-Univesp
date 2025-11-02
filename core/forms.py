# core/forms.py
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

import re
from django.core.exceptions import ValidationError

from .models import CustomUser, Paciente  # Importação única

LETRAS_SENHA = [
    ("E", "Exames"),
    ("C", "Curativos"),
    ("P", "Psicologia"),
    ("G", "Geral"),
    ("D", "Dentista"),
    ("A", "Primeiro Atendimento"),
    ("NH", "Hansenologia"),
    ("H", "Hansenologia Retorno"),
    ("U", "Ultrassom"),
]


class CadastrarPacienteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        profissionais_de_saude = kwargs.pop("profissionais_de_saude", None)
        super().__init__(*args, **kwargs)
        if profissionais_de_saude:
            self.fields["profissional_saude"].queryset = profissionais_de_saude

    profissional_saude = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(funcao="profissional_saude"),
        label="Profissional de Saúde",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    tipo_senha = forms.ChoiceField(
        choices=LETRAS_SENHA,
        label="Tipo de Senha",
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def clean_telefone_celular(self):
        val = self.cleaned_data.get("telefone_celular", "") or ""
        import re

        digits = re.sub(r"\D+", "", val)[:11]  # só dígitos, no máx 11
        # opcional: exigir 11 dígitos começando com 9 no 3º
        if digits and not (len(digits) == 11 and digits[2] == "9"):
            raise forms.ValidationError(
                "Informe um celular válido com DDD e 9 dígitos."
            )
        return digits

    def clean_nome_completo(self):
        nome_completo = self.cleaned_data.get("nome_completo")
        if nome_completo and "<script" in nome_completo.lower():
            raise forms.ValidationError("Entrada inválida: scripts não são permitidos.")
        return nome_completo

    def clean_cartao_sus(self):
        cartao_sus = self.cleaned_data.get("cartao_sus")
        if cartao_sus:
            # Verifica se já existe um paciente com este cartão SUS
            if Paciente.objects.filter(cartao_sus=cartao_sus).exists():
                raise forms.ValidationError(
                    "Já existe um paciente cadastrado com este cartão SUS."
                )
        return cartao_sus

    class Meta:
        model = Paciente
        fields = [
            "nome_completo",
            "cartao_sus",
            "horario_agendamento",
            "profissional_saude",
            "observacoes",
            "tipo_senha",
            "telefone_celular",
        ]

        help_texts = {
            "telefone_celular": None,
        }

        widgets = {
            "horario_agendamento": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "telefone_celular": forms.TextInput(
                attrs={
                    "type": "text",
                    "placeholder": "(99) 9 9999-9999",
                    "inputmode": "numeric",
                    "autocomplete": "tel",
                    "title": "Informe um celular válido, ex.: (99) 9 9999-9999",
                }
            ),
        }


class CadastrarFuncionarioForm(UserCreationForm):
    import re

    @staticmethod
    def validate_cpf(value):
        # Remove caracteres não numéricos
        digits = re.sub(r"\D", "", value)

        # Verifica se tem exatamente 11 dígitos
        if len(digits) != 11:
            raise ValidationError("CPF deve ter exatamente 11 dígitos.")

        # Verifica se todos os dígitos são iguais (CPF inválido)
        if digits == digits[0] * 11:
            raise ValidationError("CPF inválido.")

        # Calcula o primeiro dígito verificador
        sum1 = sum(int(digits[i]) * (10 - i) for i in range(9))
        digit1 = (sum1 * 10) % 11
        if digit1 == 10:
            digit1 = 0

        # Calcula o segundo dígito verificador
        sum2 = sum(int(digits[i]) * (11 - i) for i in range(10))
        digit2 = (sum2 * 10) % 11
        if digit2 == 10:
            digit2 = 0

        # Verifica se os dígitos calculados batem com os informados
        if int(digits[9]) != digit1 or int(digits[10]) != digit2:
            raise ValidationError("CPF inválido.")

        return value

    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        help_text="Digite o cpf sem pontos ou traços.",
        validators=[validate_cpf],
    )
    funcao = forms.ChoiceField(
        choices=CustomUser.FUNCAO_CHOICES,
        help_text="Selecione a função do funcionário.",
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("cpf", "username", "first_name", "last_name", "email", "funcao")
        help_texts = {
            "username": None,
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if "<script" in first_name.lower():
            raise forms.ValidationError("Entrada inválida: scripts não são permitidos.")
        return first_name

    def save(self, commit=True):
        user = super().save(commit=False)
        user = super(UserCreationForm, self).save(commit=False)
        user.username = self.cleaned_data["cpf"]  # Define o username como o CPF
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(attrs={"placeholder": "Digite seu CPF"}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Digite sua senha"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        cpf = cleaned_data.get("cpf")
        password = cleaned_data.get("password")

        if cpf and password:
            try:
                user = CustomUser.objects.get(cpf=cpf)
            except CustomUser.DoesNotExist:
                user = None

            if user:
                # Verificar se o usuário está bloqueado
                if user.lockout_until and timezone.now() < user.lockout_until:
                    remaining_time = (
                        user.lockout_until - timezone.now()
                    ).total_seconds() / 60
                    raise ValidationError(
                        f"Conta bloqueada. Tente novamente em {int(remaining_time)} minutos."
                    )

                # Tentar autenticar
                user_auth = authenticate(username=cpf, password=password)
                if user_auth and user_auth.is_active:
                    cleaned_data["user"] = user_auth
                    # Resetar tentativas em login bem-sucedido
                    user.failed_login_attempts = 0
                    user.save()
                else:
                    # Incrementar tentativas falhidas
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 4:
                        user.lockout_until = timezone.now() + timezone.timedelta(
                            minutes=5
                        )
                        user.save()
                        raise ValidationError(
                            "Conta bloqueada por tentativas excessivas. Tente novamente em 5 minutos."
                        )
                    else:
                        user.save()
                        raise ValidationError("CPF ou senha incorretos.")
            else:
                raise ValidationError("CPF ou senha incorretos.")

        return cleaned_data
