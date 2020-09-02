# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


with open("README.md") as f:
    readme = f.read()


setup(
    name="neuromation",
    version="20.9.2",
    python_requires=">=3.6.0",
    # Make sure to pin versions of install_requires
    install_requires=[
        "aiohttp>=3.6.2",
        'dataclasses>=0.5; python_version<"3.7"',
        "pyyaml>=3.0",
        'async-generator>=1.5; python_version<"3.7"',
        'async-exit-stack>=1.0.1; python_version<"3.7"',
        "python-jose>=3.0.0",
        "python-dateutil>=2.7.0",
        "yarl>=1.5.1",
        "multidict>=4.0",
        "aiodocker>=0.18.7",
        "click>=7.0",
        "humanize>=0.5",
        "typing_extensions>=3.7.4",
        # certifi has no version requirement
        # CLI raises a warning for outdated package instead
        "certifi",
        "cookiecutter>=0.9.0",
        "atomicwrites>=1.0",
        "wcwidth>=0.1.7",
        "toml>=0.10.0",
        "prompt-toolkit>=3.0.5",
    ],
    include_package_data=True,
    description="Neuro Platform API client",
    long_description=readme,
    long_description_content_type="text/markdown; charset=UTF-8; variant=GFM",
    author="Neuromation Team",
    author_email="pypi@neuromation.io",  # TODO: change this email
    license="Apache License, version 2.0",
    url="https://neuromation.io/",
    packages=find_packages(include=("neuromation", "neuromation.*")),
    entry_points={
        "console_scripts": [
            "neuro=neuromation.cli:main",
            "docker-credential-neuro=neuromation.cli:dch",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
    ],
)
