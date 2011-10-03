from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponsePermanentRedirect, Http404
from donation.forms import StandardDonationForm
from donation.models import Donation
from etc import cache
from etc.view_helpers import render, render_string, json_error, json_response, render_inclusiontag
from etc.decorators import AccountRequired
from etc.middleware import secure
from issue.models import Issue
import json
import logging
from org.models import Org
from users.models import User
#from utils.donations.nfg_api import NFGException
from utils import fb_helpers
from utils.misc_helpers import send_admins_error_email
from org.forms import ManageOrgForm, ManageOrgConnectForm, ManageOrgMoreForm, CreateOrgForm, DetailsOrgForm
from django.shortcuts import get_object_or_404, redirect

def old_orgname_permalink(request, orgname):
    try:
        o = Org.objects.get(name__iexact = orgname.lower())
        return HttpResponsePermanentRedirect(reverse('entity_url', args=[o.handle]))
    except:
        raise Http404

def old_org_permalink(request, mongo_id):
    try:
        o = Org.objects.get(mongo_id = mongo_id)
        return HttpResponsePermanentRedirect(reverse('entity_url', args=[o.handle]))
    except:
        raise Http404


@AccountRequired
def create_org(request):
    if request.POST:
        form = CreateOrgForm(request.POST)
        if form.is_valid():
            org = form.save()
            org.admins.add(request.user)
            return redirect('details_org', org.id)
    else:
        form = CreateOrgForm()

    return render(request, 'org/create.html', {
        'title': 'Add an organization',
        'form': form,
    })

@AccountRequired
def details(request, org_id):
    org = get_object_or_404(Org, id=org_id)
    if not org.is_editable_by(request.user):
        raise Http404

    if request.POST:
        form = DetailsOrgForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect('manage_org', org.id)
    else:
        form = DetailsOrgForm(instance=org)

    return render(request, 'org/details.html', {
        'form': form,
        'org': org,
    })

@AccountRequired
def manage_org(request, org_id, tab='about'):
    try:
        org = cache.get(Org, org_id)
    except Exception, inst:
        raise Http404
    if not org.is_editable_by(request.user):
        raise Http404

    if tab == 'about':
        form_class = ManageOrgForm
        form_url = reverse('manage_org', args=[org_id])
    elif tab == 'connect':
        form_class = ManageOrgConnectForm
        form_url = reverse('manage_org_connect', args=[org_id])
    elif tab == 'more':
        form_class = ManageOrgMoreForm
        form_url = reverse('manage_org_more', args=[org_id])

    success = False
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=org)
        if form.is_valid():
            form.save()
            success = True
    else:
        form = form_class(instance=org)

    return render(request, 'org/manage.html', {
        'title': 'Manage',
        'entity': org,
        'form': form,
        'form_url': form_url,
        'tab': tab,
        'success': success,
    })

@secure
def donate(request, handle):
    initial_amount = int(request.GET.get("amount", 0))
    initial_user = request.user if not request.user.is_anonymous() else None
    org = Org.objects.get(handle = handle)
    form = StandardDonationForm(initial_amount=initial_amount,initial_user=initial_user)

    if request.POST:
        form = StandardDonationForm(data=request.POST)
        if form.is_valid():
            donation_data = form.to_donation_data(org)
            try:
                donation = Donation.create_and_process(**donation_data)

                try:
                    #Post To Facebook
                    if form.cleaned_data.get("post_to_facebook") and initial_user:
                        fb_helpers.post_donation_to_wall(initial_user, org)
                    #Post To Stream
                    #if form.cleaned_data.get("list_name_publicly") and initial_user:
                        #FeedStream.post_new_donation(actor=initial_user, target=org, donation_id=donation.id)

                except Exception, ex:
                    logging.exception("FAILED TO SEND DONATE NOTIFICATION")
                    send_admins_error_email("FAILED TO SEND DONATE NOTIFICATION", ex.message, sys.exc_info())

                share_url = reverse('donate_share', args=[org.id])
		return HttpResponseRedirect("%s?amount=%s" % (share_url, donation.amount))

            #except NFGException, err:
            #    logging.exception("NFG ERROR PROCESSING STANDARD DONATION")
            #    if err.message.get("error_details"):
            #        form.handle_nfg_errors(err.message["error_details"])
            #    else:
            #        form.handle_unknown_error()
            except Exception, err:
                logging.exception("ERROR PROCESSING STANDARD DONATION")
                form.handle_unknown_error()

    return render(request, 'org/donate.html', {
            'type':'org_donate',
            'form' : form,
            'org' : org,
            'title' : org.get_name
            })


def share(request, org_id):
    amount = request.GET.get('amount', None)
    org = Org.objects.get(id = org_id)

    return render(request, 'org/donate_success.html', {
            'amount':amount,
            'org':org,
            'title':'Share your donation to %s' % org.get_name
            })


@AccountRequired
def claim_org(request, org_id):
    try:
        org = Org.objects.get(id = org_id)
    except:
        raise Http404

    return render(request, 'org/claim.html', {'org' : org})

@AccountRequired
def claim_org_confirm(request, org_id):
    try:
        org = Org.objects.get(id = org_id)
    except:
        raise Http404

    return render(request, 'org/claimed.html', {'org' : org})


# cache this bad boy for 6 hours
#@cache_page(60*360)
def org_categories(request):
    categories = Issue.objects.filter(parent_issue__isnull = True).filter(is_active = True).order_by('name')

    js_cats = ['']
    js_subcats = []
    js_issues = []

    for cat in categories:
        if len(cat.issue_set.all()) == 0:
            continue
        # FIXME: delete the following line whenever the CMS gets cleaned up
        #cat.name = ' '.join(i.capitalize() for i in cat.name.split(' '))
        js_cats.append(cat.name)
        subcats = Issue.objects.filter(parent_issue = cat).filter(is_active = True).order_by('name')
        if not subcats:
            js_subcats.append({'text':cat.name, 'when':cat.name, 'value':cat.name.lower()})
            js_issues.append({'text':cat.name, 'when':cat.name.lower(), 'value':cat.name.lower()})
        else:
            js_subcats.append({'text':cat.name, 'when':cat.name, 'value':cat.name.lower()})
            js_issues.append({'text':cat.name, 'when':cat.name.lower(), 'value':cat.name.lower()})
            for subcat in subcats:
                # FIXME: delete the following line whenever the CMS gets cleaned up
                #subcat.name = ' '.join(i.capitalize() for i in subcat.name.split(' '))
                js_subcats.append({'text':subcat.name, 'when':cat.name.lower(), 'value':subcat.name.lower()})
                issues = Issue.objects.filter(parent_issue = subcat).filter(is_active = True).order_by('name')
                if not issues:
                    js_issues.append({'text':subcat.name, 'when':subcat.name.lower(), 'value':subcat.name.lower()})
                else:
                    js_issues.append({'text':subcat.name, 'when':subcat.name.lower(), 'value':subcat.name.lower()})
                    for issue in issues:
                        # FIXME: delete the following line whenever the CMS gets cleaned up
                        #issue.name = ' '.join(i.capitalize() for i in issue.name.split(' '))
                        js_issues.append({'text':issue.name, 'when':subcat.name.lower(), 'value':issue.name.lower()})


    r = HttpResponse('var TOP_LEVEL_CATEGORIES=%s,ORG_SUB_CATEGORIES=%s,ORG_ISSUES=%s;' % (json.dumps(js_cats), json.dumps(js_subcats), json.dumps(js_issues)))
    return r

def followed_org_list(request, user_id):
    start = int(request.GET.get('start', 0))
    end = int(request.GET.get('end', 20))
    user = get_object_or_404(User, id=user_id)
    org_commitments = user.commitments.with_orgs()[start:end].fetch_generic_relations()
    orgs = [commitment.entity for commitment in org_commitments]
    num_orgs = user.commitments.with_orgs().count()

    html = render_string(request, "org/includes/followed_org_list.html", {
        'orgs': orgs,
        'start_index': start,
    })

    return json_response({
        'html': html,
        'has_more': end < num_orgs,
    })
