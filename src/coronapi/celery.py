import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coronapi.settings')

app = Celery('coronapi')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
