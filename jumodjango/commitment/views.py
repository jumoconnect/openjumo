from etc.decorators import PostOnly, AccountRequired
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, get_object_or_404
from commitment.models import Commitment
from etc.view_helpers import json_error, json_response, render_inclusiontag, render_string
from django.core.exceptions import ValidationError
from django.db.models import get_model

@AccountRequired
@PostOnly
def create(request):
    entity_id = request.POST['object_id']
    entity_type = request.POST['content_type']
    content_type = ContentType.objects.get(id=entity_type)
    entity = content_type.get_object_for_this_type(id=entity_id)
    commitment = Commitment(entity=entity, user=request.user)

    response = redirect(entity)
    try:
        commitment.full_clean()
        commitment.save()
        if request.is_ajax():
            button = render_inclusiontag(request, "commitment_button entity", "commitment_tags",
                                         {'entity': entity})
            actions = render_string(request, "action/includes/action_list.html", {
                'entity': entity,
                'actions': entity.actions.all(),
            })
            response = json_response({'button': button, 'actions': actions})
    except ValidationError:
        if request.is_ajax():
            response = json_error(400, "You have already committed to this issue/org.")
    return response

@AccountRequired
@PostOnly
def delete(request, commitment_id):
    commitment = get_object_or_404(Commitment, user=request.user, id=commitment_id)
    commitment.delete()

    response = redirect(commitment.entity)
    if request.is_ajax():
        button = render_inclusiontag(request, "commitment_button entity", "commitment_tags",
                                     {'entity': commitment.entity})
        response = json_response({'button': button})
    return response

def list(request, entity_id, model_name):
    start = int(request.GET.get('start', 0))
    end = int(request.GET.get('end', 20))
    model = get_model(*model_name.split('.'))
    entity = get_object_or_404(model, id=entity_id)
    commitments = entity.commitments.active()[start:end].select_related()

    html = render_string(request, "commitment/includes/committer_list.html", {
        'commitments': commitments,
        'start_index': start,
    })

    return json_response({
        'html': html,
        'has_more': end < entity.commitments.count(),
    })
