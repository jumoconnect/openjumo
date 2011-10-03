from django.forms.widgets import Widget
from django.template.loader import render_to_string
from entity_items.models.location import Location
from django.utils.encoding import force_unicode

class LocationWidget(Widget):
    def render(self, name, value, attrs=None):
        location_name = location_data = ''
        try:
            location = Location.objects.get(id=value)
            location_name = str(location)
            location_data = location.to_json()
        except Location.DoesNotExist:
            pass

        return render_to_string('widgets/location_widget.html', {
            'location_name': location_name,
            'location_data': location_data,
            'name': name,
        })

    def value_from_datadict(self, data, files, name):
        location_data = data.get(name)
        location = Location.get_or_create(location_data)
        if location:
            return location.id
        return None

class MultipleLocationWidget(Widget):
    def render(self, name, value, attrs=None):
        if value is None: value = []
        locations = Location.objects.in_bulk(value)
        location_data = []
        for (id, location) in locations.iteritems():
            location_data.append((str(location), location.to_json()))

        return render_to_string('widgets/working_locations.html', {
            'location_data': location_data,
            'name': name,
        })

    def value_from_datadict(self, data, files, name):
        location_data = data.getlist(name)
        location_ids = []
        for data in location_data:
            if not data: continue
            location = Location.get_or_create(data)
            location_ids.append(location.id)
        return location_ids

    def _has_changed(self, initial, data):
        if initial is None:
            initial = []
        if data is None:
            data = []
        if len(initial) != len(data):
            return True
        initial_set = set([force_unicode(value) for value in initial])
        data_set = set([force_unicode(value) for value in data])
        return data_set != initial_set
