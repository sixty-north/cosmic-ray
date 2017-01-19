import io
import os
import re
from setuptools import setup, find_packages
import sys


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


operators = [
    'number_replacer = '
    'cosmic_ray.operators.number_replacer:NumberReplacer',

    'mutate_comparison_operator = '
    'cosmic_ray.operators.comparison_operator_replacement:MutateComparisonOperator',

    'replace_true_false = '
    'cosmic_ray.operators.boolean_replacer:ReplaceTrueFalse',

    'replace_and_with_or = '
    'cosmic_ray.operators.boolean_replacer:ReplaceAndWithOr',

    'replace_or_with_and = '
    'cosmic_ray.operators.boolean_replacer:ReplaceOrWithAnd',

    'add_not = '
    'cosmic_ray.operators.boolean_replacer:AddNot',

    'mutate_unary_operator ='
    'cosmic_ray.operators.unary_operator_replacement:MutateUnaryOperator',

    'mutate_binary_operator ='
    'cosmic_ray.operators.binary_operator_replacement:MutateBinaryOperator',

    'break_continue_replacement ='
    'cosmic_ray.operators.break_continue:ReplaceBreakWithContinue',
]

INSTALL_REQUIRES = [
    'astunparse',
    'decorator',
    'docopt',
    'nose',
    'pathlib',
    'pytest>=3.0',
    'stevedore',
    'tinydb>=3.2.1',
    'transducer',
    'celery<4',
]

if sys.version_info < (3, 4):
    INSTALL_REQUIRES.append('enum34')

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
