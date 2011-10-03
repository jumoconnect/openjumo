from django import template
from users.models import UserToUserFollow
from django.core.urlresolvers import reverse

register = template.Library()

@register.inclusion_tag('user/includes/follow_button.html', takes_context=True)
def follow_button(context, followed):
    user = context['user']

    button_class = "button"
    button_text = "Follow"
    post_url = ""
    if user.is_authenticated():
        if UserToUserFollow.actives.filter(follower=user, followed=followed).count():
            button_class += " unfollow"
            button_text = "Unfollow"
            post_url = reverse('unfollow_user', args=[followed.id])
        else:
            button_class += " follow"
            post_url = reverse('follow_user', args=[followed.id])
    else:
        button_class += " follow login"

    button = '<input class="%s" type="submit" value="%s" data-url="%s" />' % (button_class, button_text, post_url)

    return {
        'user': user,
        'post_url': post_url,
        'button': button,
    }
