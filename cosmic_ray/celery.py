"""Central location for celery-specific stuff.
"""

from celery import Celery

app = Celery(
    'cosmic-ray',
    broker='amqp://',
    backend='amqp://')
