from django.db import models

# Create your models here.

# Reactors: Reactor Names
# fields: latitude, longitude, power output, region
class Reactor(models.Model):

    REGION_CHOICES = [
        ('I', 'Region I'),
        ('II', 'Region II'),
        ('III', 'Region III'),
        ('IV', 'Region IV'),
    ]

    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=3, choices=REGION_CHOICES)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

# unit (foreign key to React Name)
class ReactorStatus(models.Model):
    reactor = models.ForeignKey('Reactor', on_delete=models.CASCADE, null=True, blank=True)
    report_date = models.DateField()
    unit = models.CharField(max_length=30)
    power = models.IntegerField()
    down_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    changed = models.BooleanField(default=False)
    scrams = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('report_date', 'unit')

    def __str__(self):
        return f"{self.unit} - {self.report_date}"
    

# Class for StubOutage
class StubOutage(models.Model):
    reactor = models.ForeignKey('Reactor', on_delete=models.CASCADE, null=True, blank=True)
    date_detected = models.DateField()
    description = models.TextField(blank=True)
    auto_detected = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class ReactorForecast(models.Model):
    reactor = models.ForeignKey('Reactor', on_delete=models.CASCADE, null=True, blank=True)
    df = models.DateField() # Forecast date
    yhat = models.FloatField() # Predicted power
    yhat_lower = models.FloatField()
    yhat_upper = models.FloatField()
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reactor', 'created_at')
