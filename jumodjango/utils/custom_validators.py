from django.core.exceptions import ValidationError
from django.db.models import get_model

class BlankUniqueValidator(object):
    def __init__(self, app_label, model_name, field_name):
        self.app_label = app_label
        self.model_name = model_name
        self.field_name = field_name

    def __call__(self, value):
        if value:
            model = get_model(self.app_label, self.model_name)
            if model.objects.filter(**{self.field_name: value}).count() > 0:
                verbose_name = model._meta.get_field_by_name(self.field_name)[0].verbose_name
                raise ValidationError('Another %s with this %s already exists.' % (
                    model.__name__, verbose_name))
