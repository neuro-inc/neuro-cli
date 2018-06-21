# -*- coding: utf-8 -*-

# Inspired by: https://github.com/kennethreitz/setup.py

from setuptools import find_packages, setup

import neuromation

with open('README.md') as f:
    readme = f.read()

# with open('LICENSE') as f:
#     license = f.read()

setup(
    name='neuromation',
    version=neuromation.__version__,
    python_requires='>=3.5.0',
    # Make sure to pin versions of install_requires
    install_requires=[
        'aiohttp==3.2.1',
        'dataclasses==0.5',
        'docopt==0.6.2'
    ],
    include_package_data=True,
    description='Neuromation Platform API client',
    long_description=readme,
    author='Neuromation Team',
    author_email='engineering@neuromation.io',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={'console_scripts': [
        'nm=neuromation.cli:main'
    ]}
)
