"""Central location for celery-specific stuff."""

from celery import Celery

app = Celery(
    'cosmic-ray',
    broker='amqp://',
    backend='amqp://')

app.conf.CELERY_ACCEPT_CONTENT = ['json']
app.conf.CELERY_TASK_SERIALIZER = 'json'
app.conf.CELERY_RESULT_SERIALIZER = 'json'

# This will remove all pending work from the queue. We need to do this when we
# shut down during exec:
#
#     cosmic_ray.celery.app.control.purge()
