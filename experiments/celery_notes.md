To start the rabbitmq server:
```
sudo /usr/local/sbin/rabbitmq-server
```

To run the worker tasks:
```
celery -A cosmic_ray.worker worker --loglevel=info
```

Client code:
```
import cosmic_ray.worker

cosmic_ray.worker.greeting_task.delay('something')
```
