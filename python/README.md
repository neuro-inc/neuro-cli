[![codecov](https://codecov.io/gh/neuromation/platform-api-clients/branch/master/graph/badge.svg?token=FwM6ZV3gDj)](https://codecov.io/gh/neuromation/platform-api-clients)

# Welcome to Neuromation API Python client

## Hello World

```python
from neuromation import model, storage

# Authentication information is retrieved from environment
# variables or from ~/.neuromation

# Upload training dataset
#
# Option 1. Use stream as source and write it
# to file in Neuromation object storage
#
# TODO: if file exists, shall we throw or overwrite?
uri = storage.upload(
    source=open('file://~/local/file', 'rb'),
    destination='storage://~/hello_world_data/file')

# Option 2. Use local file or directory and copy it
# similar to cp -r
#
# TODO: support for globs?
uri = storage.upload(
    source='file://~/local/',
    destination='storage://~/hello_world_data/')

# Train using container image from neuromation repo
# and use a newly uploaded dataset
#
# status is a handle that contains job id and allows to:
# 1. query training process
# 2. wait for job to complete (via await)
# 3. subscribe to job completion by passing handle
# 4. retrieve job results. In case of training it is the uri
#    for model checkpoint that is passed in results argument
#    or auto-generated if results not specified or None (default)
# 5. Future: stop, pause, resume job
training_job = model.train(
    image='neuromation/hello-world',
    resources=model.Resources(memory='64G', cpu=4, gpu=4),
    dataset=uri,
    results='storage://~/hello-world/model')

# Wait for job to complete and retrieve weights uri
model_uri = training_job.wait().uri

# Upload dataset for inference from client's local file system
#
dataset_uri = storage.upload(
    source='file://~/local/dataset',
    destination='storage://~/hello_world_data/dataset')

# Run inference on newly trained model
inference_job = model.infer(
    image='neuromation/hello-world',
    resources=model.Resources(memory='16G', cpu=2, gpu=1)
    model=model_uri,
    dataset=dataset_uri,
    cmd='arg1' # Optional
    )

# Wait for job to complete and retrieve result set uri
results_uri = inference_job.wait().uri

# Download result set
storage.download(
    source=results_uri,
    destination='file://~/local/results')
```

## Errors(Exceptions)

* ClientError
  * IllegalArgumentError!!!(bultins.ValueError)
  * ResourceNotFoundError
  * AuthError
    * AuthenticationError
    * AuthorizationError
   

## Contributing

```shell
git clone https://github.com/neuromation/platform-api-clients.git
cd platform-api-clients/python
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
