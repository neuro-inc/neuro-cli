[![codecov](https://codecov.io/gh/neuro-inc/platform-client-python/branch/master/graph/badge.svg)](https://codecov.io/gh/neuro-inc/platform-client-python)

# Preface

Welcome to Python Apolo-SDK for https://console.apolo.us/.

# Documentation

https://apolo-sdk.readthedocs.io/en/latest/

# Installation


Install from PyPI:

```shell
$ pip install apolo-sdk
```

# Contributing

For OSX users install coreutils to properly interpret shell commands:

```
brew install coreutils
```

Before you begin, it is recommended to have clean virtual environment installed:

```shell
$ python -m venv .env
$ source .env/bin/activate
```

Development flow:

* Install dependencies: `make setup`
* Reformat code: `make format`
* Lint: `make lint`
* Run tests: `make test`
