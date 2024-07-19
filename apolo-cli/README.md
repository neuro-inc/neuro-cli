[![codecov](https://codecov.io/gh/neuro-cli/platform-client-python/branch/master/graph/badge.svg)](https://codecov.io/gh/neuro-cli/platform-client-python)

# Preface

Welcome to Apolo CLI tool for https://apolo.us/.
Package ship command line tool called `apolo`. With it you can:
* Execute and debug jobs
* Manipulate Data
* Make some fun

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

* Install dependencies: `make setup`
* Reformat code: `make format`
* Lint: `make lint`
* Run tests: `make test`
* Run end-to-end tests: `make e2e`
