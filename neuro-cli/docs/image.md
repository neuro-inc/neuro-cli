# image

Container image operations

## Usage

```bash
neuro image [OPTIONS] COMMAND [ARGS]...
```

Container image operations.

## Commands

* [neuro image ls](image.md#ls): List images
* [neuro image push](image.md#push): Push an image to platform registry
* [neuro image pull](image.md#pull): Pull an image from platform registry
* [neuro image rm](image.md#rm): Remove image from platform registry
* [neuro image size](image.md#size): Get image size Image name must be URL with...
* [neuro image digest](image.md#digest): Get digest of an image from remote registry...
* [neuro image tags](image.md#tags): List tags for image in platform registry

### ls

List images

#### Usage

```bash
neuro image ls [OPTIONS]
```

List images.

#### Options

| Name         | Description                 |
| ------------ | --------------------------- |
| `--help`     | Show this message and exit. |
| `-l`         | List in long format.        |
| `--full-uri` | Output full image URI.      |

### push

Push an image to platform registry

#### Usage

```bash
neuro image push [OPTIONS] LOCAL_IMAGE [REMOTE_IMAGE]
```

Push an image to platform registry.

Remote image must be `URL` with image://
scheme.
Image names can contain tag. If tags not specified 'latest' will
be
used as value.

#### Examples

```bash

$ neuro push myimage
$ neuro push alpine:latest image:my-alpine:production
$ neuro push alpine image://myfriend/alpine:shared
```

#### Options

| Name            | Description                            |
| --------------- | -------------------------------------- |
| `--help`        | Show this message and exit.            |
| `-q`, `--quiet` | Run command in quiet mode (DEPRECATED) |

### pull

Pull an image from platform registry

#### Usage

```bash
neuro image pull [OPTIONS] REMOTE_IMAGE [LOCAL_IMAGE]
```

Pull an image from platform registry.

Remote image name must be `URL` with
image:// scheme.
Image names can contain tag.

#### Examples

```bash

$ neuro pull image:myimage
$ neuro pull image://myfriend/alpine:shared
$ neuro pull image://username/my-alpine:production alpine:from-registry
```

#### Options

| Name            | Description                            |
| --------------- | -------------------------------------- |
| `--help`        | Show this message and exit.            |
| `-q`, `--quiet` | Run command in quiet mode (DEPRECATED) |

### rm

Remove image from platform registry

#### Usage

```bash
neuro image rm [OPTIONS] IMAGE
```

Remove image from platform registry.

Image name must be `URL` with image://
scheme.
Image name must contain tag.

#### Examples

```bash

$ neuro image rm image://myfriend/alpine:shared
$ neuro image rm image:myimage:latest
```

#### Options

| Name     | Description                                       |
| -------- | ------------------------------------------------- |
| `--help` | Show this message and exit.                       |
| `-f`     | Force deletion of all tags referencing the image. |

### size

Get image size Image name must be URL with...

#### Usage

```bash
neuro image size [OPTIONS] IMAGE
```

Get image size

Image name must be `URL` with image:// scheme.
Image name must
contain tag.

#### Examples

```bash

$ neuro image size image://myfriend/alpine:shared
$ neuro image size image:myimage:latest
```

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### digest

Get digest of an image from remote registry...

#### Usage

```bash
neuro image digest [OPTIONS] IMAGE
```

Get digest of an image from remote registry

Image name must be `URL` with
image:// scheme.
Image name must contain tag.

#### Examples

```bash

$ neuro image digest image://myfriend/alpine:shared
$ neuro image digest image:myimage:latest
```

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### tags

List tags for image in platform registry

#### Usage

```bash
neuro image tags [OPTIONS] IMAGE
```

List tags for image in platform registry.

Image name must be `URL` with
image:// scheme.

#### Examples

```bash

$ neuro image tags image://myfriend/alpine
$ neuro image tags -l image:myimage
```

#### Options

| Name     | Description                            |
| -------- | -------------------------------------- |
| `--help` | Show this message and exit.            |
| `-l`     | List in long format, with image sizes. |
