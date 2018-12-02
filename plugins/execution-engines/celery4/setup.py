"Setup for Cosmic Rays celery-4 engine."

import io
import os
import re
from setuptools import setup, find_packages


def read(*names, **kwargs):
    "Read the contents of a file."
    with io.open(
            os.path.join(os.path.dirname(__file__), *names),
            encoding=kwargs.get("encoding", "utf8")) as fp:
        return fp.read()


def find_version(*file_paths):
    "Find the package version from a python file."
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


long_description = read('README.md', mode='rt')

setup(
    name='cosmic-ray-celery4-engine',
    version=find_version('cosmic_ray_celery4_engine/version.py'),
    packages=find_packages(exclude=['contrib', 'docs', 'test*']),
    author='Sixty North AS',
    author_email='austin@sixty-north.com',
    description=
    'Cosmic Ray execution engine that distributes execution via Celery 4.',
    license='MIT',
    keywords='testing',
    url='http://github.com/sixty-north/cosmic-ray',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
    ],
    platforms='any',
    include_package_data=True,
    install_requires=[
        'celery>=4',
    ],
    entry_points={
        'cosmic_ray.execution_engines': [
            'celery4 = cosmic_ray_celery4_engine.engine:CeleryExecutionEngine',
        ]
    },
    long_description=long_description,
)
