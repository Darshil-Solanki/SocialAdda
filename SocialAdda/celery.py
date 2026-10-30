import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SocialAdda.settings')

app = Celery('SocialAdda')
# Settings keys are read from the Django settings module, prefixed with CELERY_.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
