import requests
from flask import request
import json
from analytics.models import Measure
from django.core.management.base import BaseCommand
from datetime import datetime
import os

 
DATE_FORMAT="%Y-%m-%dT%H:%M:%S"
START=datetime.timestamp(datetime.strptime("2017-01-01T00:00:00",DATE_FORMAT))-3600
END=datetime.timestamp(datetime.strptime("2017-01-01T00:00:00",DATE_FORMAT))
#END=datetime.timestamp(datetime.strptime("2019-01-01T00:00:00",DATE_FORMAT))
IMPORT_URL = 'https://api-recrutement.ecoco2.com/v1/data'+"?start="+str(START)+"&end="+str(END)

def import_measure(data):
    from analytics.models import Measure
    date_time = data.get('datetime', None)
    co2_rate = data.get('co2_rate', None);
    try:
        measure, created = Measure.objects.get_or_create(measure_date=date_time,measure_rate=co2_rate)
        if created:
            measure.save()
            display_format = "\nMeasure, {}, has been saved."
            print(display_format.format(measure))
    except Exception as ex:
        print(str(ex))
        msg = "\n\nSomething went wrong saving this measure: {}\n{}".format(date_time, str(ex))
        print(msg)
#def handle(*args, **options):
headers = {'Content-Type': 'application/json'}
response = requests.get(
url=IMPORT_URL,
headers=headers,
)
response.raise_for_status()
data = response.json()
for data_object in data:
    import_measure(data_object)

