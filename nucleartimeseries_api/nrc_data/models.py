from django.db import models

# Create your models here.


class Reactor(models.Model):
    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=10)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

# unit (foreign key to React Name)
class ReactorStatus(models.Model):

    REGION_CHOICES = [
        ('I', 'Region I'),
        ('II', 'Region II'),
        ('III', 'Region III'),
        ('IV', 'Region IV'),
    ]

    report_date = models.DateField()
    unit = models.CharField(max_length=30)
    power = models.IntegerField()
    down_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    changed = models.BooleanField(default=False)
    scrams = models.IntegerField(null=True, blank=True)
    region = models.CharField(max_length=3, choices=REGION_CHOICES)
    
    class Meta:
        unique_together = ('report_date', 'unit')

    def __str__(self):
        return f"{self.unit} - {self.report_date}"
    
# Reactors: Reactor Names
# fields: latitude, longitude, power output, region

# Class for StubOutage


