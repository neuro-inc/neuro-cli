[![codecov](https://codecov.io/gh/neuromation/platform-client-python/branch/master/graph/badge.svg)](https://codecov.io/gh/neuromation/platform-client-python)

# Preface

Welcome to Neuromation API Python client for https://neu.ro/.
Package ship command line tool called `neuro`. With it you can:
* Execute and debug jobs
* Manipulate Data
* Make some fun

# Api

https://neuromation-sdk.readthedocs.io/en/latest/

# Contributing

For OSX users install coreutils to properly interpret shell commands:

```
brew install coreutils
```

Before you begin, it is recommended to have clean virtual environment installed:

```shell
python -m venv .env
source .env/bin/activate
```

Development flow:

* Install dependencies: `make init`
* Reformat code: `make fmt`
* Lint: `make lint`
* Run tests: `make test`
* Run end-to-end tests: `make e2e`
