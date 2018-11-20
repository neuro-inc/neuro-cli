# -*- coding: utf-8 -*-

# Inspired by: https://github.com/kennethreitz/setup.py

from setuptools import find_packages, setup


with open('README.md') as f:
    readme = f.read()

# with open('LICENSE') as f:
#     license = f.read()

setup(
    name='neuromation',

    use_scm_version={'root': '..', 'relative_to': __file__},
    setup_requires=['setuptools_scm'],

    python_requires='>=3.5.0',
    # Make sure to pin versions of install_requires
    install_requires=[
        'aiohttp==3.4.4',
        'dataclasses==0.5',
        'docopt==0.6.2',
        'pyyaml==3.13',
        'async_generator==1.9',
        'python-jose==3.0.1',
        'python-dateutil==2.7.5',
        'keyring~=13.0',
        'keyrings.cryptfile==1.2.1'
    ],
    include_package_data=True,
    description='Neuromation Platform API client',
    long_description=readme,
    author='Neuromation Team',
    author_email='engineering@neuromation.io',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={'console_scripts': [
        'neuro=neuromation.cli:main'
    ]}
)
