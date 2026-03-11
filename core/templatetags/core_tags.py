# core/templatetags/core_tags.py
import logging

from django import template

register = template.Library()

logger = logging.getLogger(__name__)


@register.filter(name="get_proporcao_field")
def get_proporcao_field(form, field_name):
    proporcao_field_name = f'proporcao_{field_name.split("_")[-1]}'
    field = form[proporcao_field_name]
    try:
        value = field.value()
        if value is None or value == "":
            # Define o atributo 'value' para "1"
            return field.as_widget(
                attrs={
                    "class": field.field.widget.attrs.get("class", ""),
                    "value": "1",
                }
            )
        else:
            return field
    except Exception as e:
        # Em caso de erro, também retorna o campo com value="1" e registra
        logger.exception("Erro ao obter valor do campo %s: %s", proporcao_field_name, e)
        return field.as_widget(
            attrs={
                "class": field.field.widget.attrs.get("class", ""),
                "value": "1",
            }
        )


@register.filter(name="add_class")
def add_class(field, css):
    return field.as_widget(attrs={"class": css})  # Não precisa mudar essa linha
