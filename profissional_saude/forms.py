# profissional_saude/forms.py
from django import forms


class AtendimentoProfissionalForm(forms.Form):
    """
    Formulário para o profissional de saúde interagir com a senha do paciente.
    """

    paciente_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona os botões como campos para facilitar o tratamento na view
        self.fields["chamar"] = forms.BooleanField(
            required=False, widget=forms.HiddenInput()
        )
        self.fields["reanunciar"] = forms.BooleanField(
            required=False, widget=forms.HiddenInput()
        )
        self.fields["encaminhar"] = forms.BooleanField(
            required=False, widget=forms.HiddenInput()
        )
        self.fields["confirmar"] = forms.BooleanField(
            required=False, widget=forms.HiddenInput()
        )

    # Campo para selecionar o profissional de saúde para encaminhamento.
    profissional_encaminhar = forms.ModelChoiceField(
        queryset=None,  # Definido dinamicamente na view
        label="Encaminhar para:",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        acao_selecionada = False

        # Verifica se apenas uma ação (botão) foi selecionada
        if cleaned_data.get("chamar"):
            if acao_selecionada:
                raise forms.ValidationError(
                    "Selecione apenas uma ação (Chamar, Reanunciar, Encaminhar, Confirmar)."
                )
            acao_selecionada = True
        if cleaned_data.get("reanunciar"):
            if acao_selecionada:
                raise forms.ValidationError(
                    "Selecione apenas uma ação (Chamar, Reanunciar, Encaminhar, Confirmar)."
                )
            acao_selecionada = True
        if cleaned_data.get("encaminhar"):
            if acao_selecionada:
                raise forms.ValidationError(
                    "Selecione apenas uma ação (Chamar, Reanunciar, Encaminhar, Confirmar)."
                )
            acao_selecionada = True
        if cleaned_data.get("confirmar"):
            if acao_selecionada:
                raise forms.ValidationError(
                    "Selecione apenas uma ação (Chamar, Reanunciar, Encaminhar, Confirmar)."
                )
            acao_selecionada = True

        return cleaned_data
