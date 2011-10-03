from django import template
from django.template.loader import render_to_string
from commitment.models import Commitment
from commitment.forms import CommitmentForm
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from etc.view_helpers import url_with_qs
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.inclusion_tag('commitment/includes/commitment_button.html', takes_context=True)
def commitment_button(context, entity, with_popup = 1): # using 1 & 0 as bool for the templates
    user = context['user']

    d = {'button_type': 'login',
         'with_popup': with_popup,
         'button_text': ('Help Out') # %s' % entity._meta.verbose_name),
         }
    if user.is_authenticated():
        try:
            entity_type = ContentType.objects.get_for_model(entity)
            d['commitment'] = Commitment.objects.get(content_type=entity_type, object_id=entity.id, user=user)
            d['button_type'] = 'delete'
            d['button_text'] = "view actions" #"you're committed"
            url_name = "%s_action_list" % entity._meta.object_name.lower()
            d['data_url'] = reverse(url_name, args=[entity.id])
        except Commitment.DoesNotExist:
            commitment = Commitment(entity=entity)
            d['form'] = CommitmentForm(instance=commitment)
            d['button_type'] = 'create'
        except Commitment.MultipleObjectsReturned:
            d['commitment'] = Commitment.objects.filter(content_type=entity_type, object_id=entity.id, user=user)[0]
            d['button_type'] = 'delete'
            d['button_text'] = "view actions" #"you're committed"
            url_name = "%s_action_list" % entity._meta.object_name.lower()
            d['data_url'] = reverse(url_name, args=[entity.id])
    return d

@register.simple_tag
def link_to_commitments(entity):
    url_name = "%s_commitments" % str.lower(entity.__class__.__name__)
    url = reverse(url_name, kwargs={'entity_id': entity.id})
    return '<a id="committed_users" data-title="People Committed to %s" data-url="%s">%s</a>' % (entity.get_name, url, intcomma(entity.get_num_followers))
