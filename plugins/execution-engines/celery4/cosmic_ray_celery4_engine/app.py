"""Central location for celery-specific stuff."""

from celery import Celery

APP = Celery('cosmic-ray-celery4-executor')

APP.conf.CELERY_ACCEPT_CONTENT = ['pickle', 'json']
APP.conf.CELERY_TASK_SERIALIZER = 'pickle'
APP.conf.CELERY_RESULT_SERIALIZER = 'pickle'
APP.conf.CELERY_RESULT_BACKEND = 'amqp://'

# This will remove all pending work from the queue. We need to do this when we
# shut down during exec:
#
#     cosmic_ray.celery.app.control.purge()
