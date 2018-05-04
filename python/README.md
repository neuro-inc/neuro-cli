# Welcome to Neuromation API Python client

## Hello World

```python
from neuromation import model, storage

# Upload training dataset
object_path = storage.upload(
    path='/hello_world_data',
    stream=open('local/file', 'rb'))

# Train using container image from neuromation repo
# and use a newly uploaded dataset
status = model.train(
    image='neuromation/hello-world',
    dataset=object_path)

print(status.message)

# Run inference on newly trained model
response = model.infer(
    image='neuromation/hello-world'
    weights=status.weights)

print(response.data)
```

## Contributing

```shell
git clone https://github.com/neuromation/platform-api-clients.git
cd platform-api-clients/python
```

Before you begin, it is recommended to have clean virtual environment installed:

```shell
virtualenv .env -p python3
source .env/bin/activate
```

Development flow:

* Install dependencies: `make init`
* Run tests: `make test`
* Lint: `make lint`
* Publish to [pypi](https://pypi.org/project/neuromation/): `make publish`
