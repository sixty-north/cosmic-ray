"""Central location for celery-specific stuff."""

from celery import Celery

APP = Celery('cosmic-ray-celery-executor')
APP.config_from_object('celeryconfig')

APP.conf.CELERY_ACCEPT_CONTENT = ['pickle', 'json']
APP.conf.CELERY_TASK_SERIALIZER = 'pickle'
APP.conf.CELERY_RESULT_SERIALIZER = 'pickle'

# This will remove all pending work from the queue. We need to do this when we
# shut down during exec:
#
#     cosmic_ray.celery.app.control.purge()
