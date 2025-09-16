from django import forms

from core.models import Paciente


class GuicheForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for tipo_senha, tipo_senha_label in Paciente.SENHA_CHOICES:
            tipo_senha_lower = tipo_senha.lower()
            self.fields[f"tipo_senha_{tipo_senha_lower}"] = forms.BooleanField(
                label=tipo_senha_label,
                required=False,
            )
            self.fields[f"proporcao_{tipo_senha_lower}"] = forms.IntegerField(
                label=f"Proporção ({tipo_senha_label})",
                min_value=0,
                required=False,
                initial=1,  # Define o valor inicial como 1
                widget=forms.NumberInput(
                    attrs={"class": "form-control", "style": "width: 80px;"}
                ),
            )
