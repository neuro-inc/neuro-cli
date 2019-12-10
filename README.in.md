[![codecov](https://codecov.io/gh/neuromation/platform-api-clients/branch/master/graph/badge.svg?token=FwM6ZV3gDj)](https://codecov.io/gh/neuromation/platform-api-clients)

# Preface

Welcome to Neuromation API Python client.
Package ship command line tool called [_neuro_](#neuro). With [_neuro_](#neuro) you can:
* [Execute and debug jobs](#neuro-job)
* [Manipulate Data](#neuro-storage)
* Make some fun

{cli_doc}

# Api

*TODO*

# Contributing

```shell
git clone https://github.com/neuromation/platform-api-clients.git
cd platform-api-clients/python
```

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
* Run tests: `make test`
* Lint: `make lint`
* Publish to [pypi](https://pypi.org/project/neuromation/): `make publish`
