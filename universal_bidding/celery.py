import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'universal_bidding.settings')

app = Celery('universal_bidding')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

