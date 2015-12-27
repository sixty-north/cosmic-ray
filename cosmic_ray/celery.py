"""Central location for celery-specific stuff.
"""

from celery import Celery

app = Celery(
    'cosmic-ray',
    broker='amqp://',
    backend='amqp://')

app.conf.CELERY_ACCEPT_CONTENT = ['json']
app.conf.CELERY_TASK_SERIALIZER = 'json'
app.conf.CELERY_RESULT_SERIALIZER = 'json'
