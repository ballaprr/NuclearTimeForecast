import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nucleartimeseries_api.settings')

app = Celery('nucleartimeseries_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'fetch-nrc-data': {
        'task': 'nrc_data.tasks.fetch_latest_nrc_data',
        'schedule': crontab(hour=0, minute=0)
    }
}