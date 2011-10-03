from etc.view_helpers import json_response
from classifiers.related_search import RelatedSearchClassifier

classifier = RelatedSearchClassifier.get_model()

def related_searches(request):
    q = request.GET.get('q')
    if not q:
        return []
    else:
        resp = classifier.classify(q)
        return json_response(resp)