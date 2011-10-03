import json
from hashlib import md5
from miner.classifiers.location_tagger import LocationClassifier

from django.db import models
from django.db import connections
from django.forms.models import model_to_dict

CLASSIFIER_CHOICES = (('US', 'United States'),
                      ('International', 'International')
                      )

class Location(models.Model):
    id = models.AutoField(primary_key = True, db_column='location_id')
    raw_geodata = models.TextField(blank = True)
    geodata_hash = models.CharField(max_length=32, null=False)
    longitude = models.FloatField(null = True)
    latitude = models.FloatField(null = True, blank = True)
    address = models.CharField(max_length = 255, blank = True)
    region = models.CharField(max_length = 255, blank = True)
    locality = models.CharField(max_length = 255, blank = True)
    postal_code = models.CharField(max_length = 255, blank = True)
    country_name = models.CharField(max_length = 255, blank = True)
    classification = models.CharField(max_length = 50, null = True, blank=True, choices=CLASSIFIER_CHOICES)

    class Meta:
        db_table = 'locations'

    @classmethod
    def get_or_create(cls, data):
        if not data:
            return None
        data = json.loads(data)

        l = Location()
        raw_geodata = data.get('raw_geodata', '')
        l.raw_geodata = json.dumps(raw_geodata) if isinstance(raw_geodata, dict) else raw_geodata
        l.latitude = float(data.get('latitude', 0.0))
        l.longitude = float(data.get('longitude', 0.0))
        l.address = data.get('address', '')
        l.region = data.get('region', '')
        l.locality = data.get('locality', '')
        l.postal_code = data.get('postal_code', '')
        l.country_name = data.get('country_name', '')

        hash = md5(l.raw_geodata) if raw_geodata else md5(''.join([l.address, l.region, l.locality, l.postal_code, l.country_name]))
        l.geodata_hash = hash.hexdigest()

        existing = Location.objects.filter(geodata_hash = l.geodata_hash)
        if len(list(existing)) > 0:
            return existing[0]

        classifier = LocationClassifier.classify(l)
        if classifier:
            l.classifier = classifier

        l.save()
        return l


    def get_raw(self):
        if self.raw_geodata:
            try:
                return json.loads(self.raw_geodata)
            except:
                return None

    @property
    def name(self):
        """ Temp until we fix up name"""
        name = None
        raw_data = self.get_raw()
        if raw_data and 'name' in raw_data:
            name = raw_data['name']
        elif raw_data and 'raw_geodata' in raw_data:
            try:
                raw = json.loads(raw_data['raw_geodata'])
            except TypeError:
                raw = raw_data['raw_geodata']
            name = raw.get('name', None)
        return name

    def __unicode__(self):
        values = []
        separator = ' '

        if self.address:
            values.append(self.address)
            values.append(separator)

        name = self.name
        has_name = name or self.locality.strip()
        has_region = self.region and self.region != name
        has_country = self.country_name and self.country_name != name

        if name and name != self.locality.strip():
            values.append(name)
        elif self.locality.strip():
            values.append(self.locality)
            separator = ', '


        if has_name and (has_region or has_country):
            values.append(separator)

        separator = ' '

        if has_region:
            values.append(self.region)
            values.append(separator)

        if has_country:
            values.append(self.country_name)

        return ''.join(values)

    def to_json(self):
        return json.dumps(model_to_dict(self))
