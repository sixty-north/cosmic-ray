# cosmic_ray_celery4_executor

Cosmic Ray execution engine that distributes execution via Celery 4.

To use this, first install this plugin into your environment::

    python setup.py install

or::

    pip install .

Then start your worker::

    celery -A cosmic_ray_celery4_engine.worker worker --loglevel=INFO

Note that if you are using the "copy" cloning method, then you need to start the worker in the directory where you want
it to execute.

Then you need to specify "celery4" as your `cosmic-ray.distributor.name` in your configuration.

After that, everything should work! For more details/inspiration, see the Cosmic Ray
end-to-end test suite.