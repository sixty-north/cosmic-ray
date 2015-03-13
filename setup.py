from setuptools import setup, find_packages

setup(
    name = 'cosmic_ray',
    version = '0.0.0',
    packages = find_packages(),

    # metadata for upload to PyPI
    author = 'Austin Bingham',
    author_email = 'austin.bingham@gmail.com',
    description = 'Mutation testing',
    license = 'MIT',
    keywords = 'testing',
    # url =
    # downloadurl =
    # long_description
    # zip_safe=False,
    # classifiers=[
    #     'Development Status :: 4 - Beta',
    #     'Environment :: Console',
    #     'Intended Audience :: Developers',
    #     'License :: OSI Approved :: MIT License',
    #     'Operating System :: OS Independent',
    #     'Programming Language :: Python',
    #     'Topic :: Software Development :: Libraries'
    #     ],
    platforms='any',
    include_package_data=True,
    install_requires=[
        'docopt',
        'with_fixture',
    ],
    entry_points = {
        'console_scripts': [
            'cosmic-ray = cosmic_ray.app:main',
        ],
    },
)
