from django.db.models import get_model
from etc.view_helpers import json_response, render_string

def action_list(request, entity_id, model_name):
    model = get_model(*model_name.split('.'))
    entity = model.objects.get(id=entity_id)
    actions = entity.actions.all()
    html = render_string(request, 'action/includes/action_list.html', {
        'entity': entity,
        'actions': actions,
    })

    return json_response({'html': html})
