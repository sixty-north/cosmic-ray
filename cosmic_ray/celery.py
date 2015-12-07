from celery import Celery

app = Celery(
    'cosmic-ray',
    broker='amqp://',
    backend='amqp://')
