# -*- coding: utf-8 -*-

# Inspired by: https://github.com/kennethreitz/setup.py

from setuptools import find_packages, setup

with open('README.md') as f:
    readme = f.read()

# with open('LICENSE') as f:
#     license = f.read()

setup(
    name='neuromation',

    use_scm_version={'root': '..', 'relative_to': __file__},  # TODO: decide where take/store versions
    setup_requires=['setuptools_scm'],

    python_requires='>=3.5.0, <4',
    # Make sure to pin versions of install_requires
    install_requires=[
        'aiohttp==3.4.4',
        'dataclasses==0.5',
        'docopt==0.6.2',
        'docker==3.5.1',
        'pyyaml==3.13',
        'async_generator==1.9',
        'python-jose==3.0.1',
        'python-dateutil==2.7.5',
        'keyring~=13.0',
        'keyrings.cryptfile==1.2.1',
        'tqdm==4.28.1',
    ],
    include_package_data=True,
    description='Neuromation Platform API client',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='Neuromation Team',
    author_email='pypi@neuromation.io',  # TODO: change this email
    license=license,
    url='https://neuromation.io/',
    packages=find_packages(include=('neuromation', 'neuromation.*')),
    entry_points={
        'console_scripts': [
            'neuro=neuromation.cli:main'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development",
        "Topic :: Utilities",
        "License :: Other/Proprietary License"
    ],
)
