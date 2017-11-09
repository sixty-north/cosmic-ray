"""Central location for celery-specific stuff."""

from celery import Celery

APP = Celery(
    'cosmic-ray-celery-executor',
    broker='amqp://',
    backend='amqp://')

APP.conf.CELERY_ACCEPT_CONTENT = ['json']
APP.conf.CELERY_TASK_SERIALIZER = 'json'
APP.conf.CELERY_RESULT_SERIALIZER = 'json'

# This will remove all pending work from the queue. We need to do this when we
# shut down during exec:
#
#     cosmic_ray.celery.app.control.purge()
