from django.db import models


class Measure(models.Model):
    measure_date = models.DateTimeField()
    measure_rate = models.FloatField()
