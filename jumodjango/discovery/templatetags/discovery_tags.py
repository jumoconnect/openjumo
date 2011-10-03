from django import template

register = template.Library()

@register.simple_tag
def temp(adminform):
    print adminform.model_admin.opts
    return 'hello'
