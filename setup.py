"""Setup for Cosmic Ray.
"""
import io
import os

from setuptools import setup, find_packages


def local_file(*name):
    "Find a file relative to this directory."
    return os.path.join(os.path.dirname(__file__), *name)


def read(name, **kwargs):
    "Read the contents of a file."
    with io.open(name, encoding=kwargs.get("encoding", "utf8")) as handle:
        return handle.read()


# This is unfortunately duplicated from scripts/cosmic_ray_tooling.py. I
# couldn't find a way to use the original version and still have tox
# work...hmmm...
def read_version():
    "Read the `(version-string, version-info)` from `src/cosmic_ray/version.py`."
    version_file = local_file('src', 'cosmic_ray', 'version.py')
    local_vars = {}
    with open(version_file) as handle:
        exec(handle.read(), {}, local_vars)  # pylint: disable=exec-used
    return (local_vars['__version__'], local_vars['__version_info__'])


LONG_DESCRIPTION = read(local_file('README.rst'), mode='rt')

INSTALL_REQUIRES = [
    'astunparse',
    'decorator',
    'docopt_subcommands>=3.0.0',
    'exit_codes',
    'gitpython',
    'parso',
    'pathlib',
    'qprompt',
    'spor>=1.1.0',
    'stevedore',
    'toml',
    'virtualenv',
    'yattag',
]

version = read_version()[0]

setup(
    name='cosmic_ray',
    version=version,
    packages=find_packages('src'),
    author='Sixty North AS',
    author_email='austin@sixty-north.com',
    description='Mutation testing',
    license='MIT License',
    keywords='testing',
    package_dir={'': 'src'},
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
    install_requires=INSTALL_REQUIRES,
    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'test': ['hypothesis', 'pytest', 'pytest-mock', 'tox'],
        'dev': ['pylint', 'autopep8'],
        'docs': ['sphinx', 'sphinx_rtd_theme'],
        'celery4_engine': ['cosmic_ray_celery4_engine'],
    },
    entry_points={
        'console_scripts': [
            'cosmic-ray = cosmic_ray.cli:main',
            'cr-html = cosmic_ray.tools.html:report_html',
            'cr-report = cosmic_ray.tools.report:report',
            'cr-rate = cosmic_ray.tools.survival_rate:format_survival_rate',
            'cr-xml = cosmic_ray.tools.xml:report_xml',
        ],
        'cosmic_ray.test_runners': [
            'unittest = cosmic_ray.testing.unittest_runner:UnittestRunner',
        ],
        'cosmic_ray.operator_providers': [
            'core = cosmic_ray.operators.provider:OperatorProvider',
        ],
        'cosmic_ray.execution_engines': [
            'local = cosmic_ray.execution.local:LocalExecutionEngine',

        ],
        'cosmic_ray.interceptors': [
            'spor = cosmic_ray.interceptors.spor:intercept',
        ],
    },
    long_description=LONG_DESCRIPTION,
)
