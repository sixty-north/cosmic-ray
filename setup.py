"""Setup for Cosmic Ray.
"""

from pathlib import Path

from setuptools import setup, find_packages


INSTALL_REQUIRES = [
    "aiohttp",
    "anybadge",
    "astunparse",
    "click",
    "decorator",
    "exit_codes",
    "gitpython",
    "parso",
    "pathlib",
    "qprompt",
    "rich",
    "sqlalchemy",
    "stevedore",
    "toml",
    "virtualenv<=16.7.10",
    "yattag",
]

setup(
    name="cosmic_ray",
    version="8.3.3",
    packages=find_packages("src"),
    author="Sixty North AS",
    author_email="austin@sixty-north.com",
    description="Mutation testing",
    license="MIT License",
    keywords="testing",
    package_dir={"": "src"},
    url="http://github.com/sixty-north/cosmic-ray",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.5",
    platforms="any",
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        "test": ["hypothesis", "pytest", "pytest-mock"],
        "dev": ["flake8", "black", "bumpversion", "twine"],
        "docs": ["sphinx", "sphinx_rtd_theme"],
    },
    entry_points={
        "console_scripts": [
            "cosmic-ray = cosmic_ray.cli:main",
            "cr-html = cosmic_ray.tools.html:report_html",
            "cr-report = cosmic_ray.tools.report:report",
            "cr-badge = cosmic_ray.tools.badge:generate_badge",
            "cr-rate = cosmic_ray.tools.survival_rate:format_survival_rate",
            "cr-xml = cosmic_ray.tools.xml:report_xml",
            "cr-filter-operators = cosmic_ray.tools.filters.operators_filter:main",
            "cr-filter-pragma = cosmic_ray.tools.filters.pragma_no_mutate:main",
            "cr-filter-git = cosmic_ray.tools.filters.git:main",
            "cr-http-workers = cosmic_ray.tools.http_workers:main",
        ],
        "cosmic_ray.test_runners": [
            "unittest = cosmic_ray.testing.unittest_runner:UnittestRunner",
        ],
        "cosmic_ray.operator_providers": [
            "core = cosmic_ray.operators.provider:OperatorProvider",
        ],
        "cosmic_ray.distributors": [
            "http = cosmic_ray.distribution.http:HttpDistributor",
            "local = cosmic_ray.distribution.local:LocalDistributor",
        ],
    },
    long_description=Path("README.rst").read_text(encoding="utf-8"),
)
