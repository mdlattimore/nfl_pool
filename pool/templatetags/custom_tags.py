from django import template

register = template.Library()

@register.filter
def _zip(a, b):
    return zip(a, b)


@register.filter
def disable_if_closed(field, is_open):
    """
    Renders a form field as a widget with 'disabled' if is_open is False.
    """
    if is_open:
        return field
    return field.as_widget(attrs={'disabled': 'disabled'})