from action.models import Action
from django.contrib import admin
from django.forms import ModelForm
from org.models import Org
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db.models.fields.related import ManyToOneRel

class AdminActionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdminActionForm, self).__init__(*args, **kwargs)
        try:
            entity_model = self.instance.content_type.model_class()
        except:
            entity_model = Org
        self.fields['entity_id'].widget = ForeignKeyRawIdWidget(rel=ManyToOneRel(entity_model, 'id'))


class ActionAdmin(admin.ModelAdmin):
    list_display = ('title', 'link', 'content_type', 'entity', 'rank')

#admin.site.register(Action, ActionAdmin)
