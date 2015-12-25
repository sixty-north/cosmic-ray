from setuptools import setup, find_packages

from cosmic_ray.operators.relational_operator_replacement \
    import relational_operator_pairs

with open('README.md', 'rt') as readme:
    long_description = readme.read()


relational_replacement_operators = [
    'replace_{0}_with_{1} = '
    'cosmic_ray.operators.relational_operator_replacement:'
    'Replace{0}With{1}'.format(
        from_op.__name__, to_op.__name__)
    for (from_op, to_op) in relational_operator_pairs()]

operators = [
    'number_replacer = '
    'cosmic_ray.operators.number_replacer:NumberReplacer',

    'arithmetic_operator_deletion ='
    'cosmic_ray.operators.arithmetic_operator_deletion:ReverseUnarySub',

    'break_continue_replacement ='
    'cosmic_ray.operators.break_continue:ReplaceBreakWithContinue',
] + relational_replacement_operators

setup(
    name='cosmic_ray',
    version='0.1.2',
    packages=find_packages(),

    author='Sixty North AS',
    author_email='austin@sixty-north.com',
    description='Mutation testing',
    license='MIT License',
    keywords='testing',
    url = 'http://github.com/sixty-north/cosmic-ray',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
    ],
    platforms='any',
    include_package_data=True,
    install_requires=[
        'celery',
        'decorator',
        'docopt',
        'pykka',
        'stevedore',
        'transducer',
        'with_fixture',
    ],
    entry_points={
        'console_scripts': [
            'cosmic-ray = cosmic_ray.cli:main',
        ],
        'cosmic_ray.test_runners': [
            'unittest = cosmic_ray.testing.unittest_runner:UnittestRunner',
            'pytest = cosmic_ray.testing.pytest_runner:PytestRunner',
        ],
        'cosmic_ray.operators': operators,
    },
    long_description=long_description,
)
