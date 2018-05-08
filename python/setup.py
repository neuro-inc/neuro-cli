# -*- coding: utf-8 -*-

# Inspired by: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

# with open('LICENSE') as f:
#     license = f.read()

setup(
    name='neuromation',
    version='0.1.0',
    python_requires='>=3.5.0',
    install_requires=[],
    include_package_data=True,
    description='Neuromation Platform API client',
    long_description=readme,
    author='Neuromation Team',
    author_email='engineering@neuromation.io',
    # TODO (artyom 05/04/2018): make repo public and update URL
    # url='https://bitbucket.org/gokarousel/scheduler',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={'console_scripts': [
        # TODO (artyom, 05/07/2018): possibly add cli
        # 'nm=neuromation.cli:main'
    ]}
)
