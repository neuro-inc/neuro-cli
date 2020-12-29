Using secrets
=============

Secret is a named encrypted data stored in the Neuro Platform Cluster.

A user can create a secret, list available secret names and delete unused secrets
but the reading of secret's data back is forbidden.  Instead of bare reading,
secrets can be accessed from a running job as environment variable or mounted
file.

Secrets are isolated and user-specific, a secret that belongs to user A cannot be
accessed by user B.

Secrets management
------------------

Use `neuro secret` command group for managing secrets.

`neuro secret ls` prints all available secret names.

`neuro secret add key value` creates a secret named *key* with encrypted data
*value*.

To store the file's content as a secret please use
`neuro secret add KEY_NAME @path/to/file.txt` notation.

`neuro secret rm key` removes the secret *key*.

Internally, Neuro Platform uses Kubernetes Cluster secrets subsystem a secrets
storage.

Secrets usage
-------------

As said above, you cannot read a secret directly but should pass it into a running
job as an environment variable or mounted file.

To pass a secret *key* as environment variable please use `secret:key` as a value,
e.g. `neuro run --env VAR=secret:key ...` form.

To mount a secret as a file please use `secret:` volume's schema, e.g.
`neuro run --volume secret:key:/mount/path/file.txt`.