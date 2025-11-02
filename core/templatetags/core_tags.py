# core/templatetags/core_tags.py
from django import template

register = template.Library()


@register.filter(name="get_proporcao_field")
def get_proporcao_field(form, field_name):
    proporcao_field_name = f'proporcao_{field_name.split("_")[-1]}'
    field = form[proporcao_field_name]
    try:
        value = field.value()
        if value is None or value == "":
            # Define o atributo 'value' para "1"
            return field.as_widget(
                attrs={"class": field.field.widget.attrs.get("class", ""), "value": "1"}
            )
        else:
            return field
    except:
        # Em caso de erro, também retorna o campo com value="1"
        return field.as_widget(
            attrs={"class": field.field.widget.attrs.get("class", ""), "value": "1"}
        )


@register.filter(name="add_class")
def add_class(field, css):
    return field.as_widget(attrs={"class": css})  # Não precisa mudar essa linha
