# -*- coding: utf-8 -*-

import re

from setuptools import find_packages, setup


with open("README.md") as f:
    readme = f.read()


with open("neuromation/__init__.py") as f:
    txt = f.read()
    try:
        version = re.findall(r'^__version__ = "([^"]+)"\r?$', txt, re.M)[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")


# TODO: Add license
license = None
# with open('LICENSE') as f:
#     license = f.read()

setup(
    name="neuromation",
    version=version,
    python_requires=">=3.6.0",
    # Make sure to pin versions of install_requires
    install_requires=[
        "aiohttp>=3.0",
        'dataclasses>=0.5; python_version<"3.7"',
        "pyyaml>=3.0",
        'async_generator>=1.5; python_version<"3.7"',
        "python-jose>=3.0.0",
        "python-dateutil>=2.7.0",
        "yarl>=1.3.0",
        "aiodocker>=0.14.0",
        "click>=7.0",
        "colorama>=0.4",
        "humanize>=0.5",
        # should upgrade the version after every certify release.
        # This is very serious security point
        "certifi>=2018.11.29",
    ],
    include_package_data=True,
    description="Neuromation Platform API client",
    long_description=readme,
    long_description_content_type="text/markdown; charset=UTF-8; variant=GFM",
    author="Neuromation Team",
    author_email="pypi@neuromation.io",  # TODO: change this email
    license=license,
    url="https://neuromation.io/",
    packages=find_packages(include=("neuromation", "neuromation.*")),
    entry_points={"console_scripts": ["neuro=neuromation.cli:main"]},
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
        "License :: Other/Proprietary License",
    ],
)
