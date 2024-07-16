Using secrets
=============

A *secret* is a piece of encrypted named data stored in the Apolo Platform Cluster.

Users can create secrets, list available secret names, and delete unused secrets.
However, reading the secret's data back is impossible. Instead of plain reading,
secrets can be accessed from a running job as an environment variable or a mounted
file.

Secrets are isolated and user-specific - a secret that belongs to user A cannot be
accessed by user B.

Managing secrets
----------------

Use the `apolo secret` command group to manage secrets.

`apolo secret ls` prints all available secret names.

`apolo secret add key value` creates a secret named *key* with encrypted data
*value*.

To store a file's content as a secret, use the
`apolo secret add KEY_NAME @path/to/file.txt` notation.

`apolo secret rm key` removes the secret named *key*.

Internally, the Apolo Platform uses the Kubernetes Cluster secrets subsystem to
store secrets.

Using secrets
-------------

As said above, you can't read a secret directly, but instead should pass it to a
running job as an environment variable or a mounted file.

To pass a secret named *key* as an environment variable, use `secret:key` as a value
for `--env`.  For example, `apolo run --env VAR=secret:key ...`.

To mount a secret as a file, use the `secret:` scheme of `--volume`.
For example, `apolo run --volume secret:key:/mount/path/file.txt`.