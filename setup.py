import io
import os
import re
from setuptools import setup, find_packages
import sys

from cosmic_ray.operators.relational_operator_replacement \
    import relational_operator_pairs


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


long_description = read('README.md', mode='rt')


relational_replacement_operators = [
    'replace_{0}_with_{1} = '
    'cosmic_ray.operators.relational_operator_replacement:'
    'Replace{0}With{1}'.format(
        from_op.__name__, to_op.__name__)
    for (from_op, to_op) in relational_operator_pairs()]

operators = [
    'number_replacer = '
    'cosmic_ray.operators.number_replacer:NumberReplacer',

    'boolean_replacer = '
    'cosmic_ray.operators.boolean_replacer:BooleanReplacer',

    'arithmetic_operator_deletion ='
    'cosmic_ray.operators.arithmetic_operator_deletion:ReverseUnarySub',

    'break_continue_replacement ='
    'cosmic_ray.operators.break_continue:ReplaceBreakWithContinue',
] + relational_replacement_operators

INSTALL_REQUIRES = [
    'astunparse',
    'decorator',
    'docopt',
    'pathlib',
    'pytest',
    'stevedore',
    'tinydb',
    'transducer',
]

if sys.version_info >= (3,4):
    INSTALL_REQUIRES.append('celery')
else:
    INSTALL_REQUIRES.append('celery<4')

setup(
    name='cosmic_ray',
    version=find_version('cosmic_ray/version.py'),
    packages=find_packages(),

    author='Sixty North AS',
    author_email='austin@sixty-north.com',
    description='Mutation testing',
    license='MIT License',
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
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
    ],
    platforms='any',
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': [
            'cosmic-ray = cosmic_ray.cli:main',
        ],
        'cosmic_ray.test_runners': [
            'nose = cosmic_ray.testing.nose_runner:NoseRunner',
            'unittest = cosmic_ray.testing.unittest_runner:UnittestRunner',
            'pytest = cosmic_ray.testing.pytest_runner:PytestRunner',
        ],
        'cosmic_ray.operators': operators,
    },
    long_description=long_description,
)
