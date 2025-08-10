from django import template

register = template.Library()

@register.filter
def _zip(a, b):
    return zip(a, b)