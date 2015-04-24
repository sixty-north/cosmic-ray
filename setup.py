from setuptools import setup, find_packages

with open('README.md', 'rt') as readme:
    long_description = readme.read()

setup(
    name='cosmic_ray',
    version='0.1.0',
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
        'decorator',
        'docopt',
        'stevedore',
        'with_fixture',
    ],
    entry_points={
        'console_scripts': [
            'cosmic-ray = cosmic_ray.app:main',
        ],
        'cosmic_ray.test_runners': [
            'unittest = cosmic_ray.testing.unittest_runner:UnittestRunner',
        ],
        'cosmic_ray.operators': [
            'number_replacer = '
            'cosmic_ray.operators.number_replacer:NumberReplacer',
            'relational_operator_replacement ='
            'cosmic_ray.operators.relational_operator_replacement:create_operator',
            'arithmetic_operator_deletion ='
            'cosmic_ray.operators.arithmetic_operator_deletion:ReverseUnarySub',
        ],
    },
    long_description=long_description
)
