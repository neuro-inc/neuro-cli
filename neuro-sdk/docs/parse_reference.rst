================
Parser Reference
================


.. currentmodule:: neuro_sdk


Parser
======

.. class:: Parser

   A set of parsing helpers, useful for building helper dataclasses from string
   representations.

   .. method:: volume(volume: str) -> Volume

      Parse *volume* string into :class:`Volume` object.

      The string is a three fields separated by colon characters (``:``):
      ``<storage-uri:container-path[:ro]>``.

      *storage-uri* is a URL on local storage, e.g. ``storage:folder`` points on
      ``<user-root>/folder`` directory.

      *container-path* is a path inside a job where *storage-url* is mounted.

      Optional *ro* means that *storage-url* is mounted in *read-only* mode. Writable
      mode is used if *ro* is omitted.

      :raise: :exc:`ValueError` if *volume* has invalid format.

   .. method:: local_image(image: str) -> LocalImage

      Parse *image* string into :class:`LocalImage`.

      The string should fit to the following pattern: ``name[:tag]``,
      e.g. ``"ubuntu:latest"``.

      :raise: :exc:`ValueError` if *image* has invalid format.

   .. method:: remote_image(image: str) -> RemoteImage

      Parse *image* string into :class:`RemoteImage`.

      The string should fit to ``name[:tag]`` or ``image:name[tag]`` patterns,
      e.g. ``"ubuntu:latest"`` or ``image:my-image:latest``. The former is used for
      public DockerHub_ images, the later is for Neuro image registry.

      :raise: :exc:`ValueError` if *image* has invalid format.

  .. _DockerHub: https://hub.docker.com

   .. method:: envs(env: Sequence[str], env_file: Sequence[str] = ()) -> EnvParseResult

      Parse a sequence of *env* variables and a sequence of *env_file* file names.

      :param ~typing.Sequence[str] env: Sequence of *env* variable specification. Each
                                        element can be either:
                                        - `ENV_NAME`. Current system *env* variable value
                                        will be used. Defaults to empty string.
                                        - `ENV_NAME=VALUE`. Given value will be used.

      :param ~typing.Sequence[str] env_file: Sequence of ``.env`` files to use. File content
                                             processed same way as *env* parameter.

      :return: :class:`EnvParseResult` with parsing result

   .. method:: volumes(volume: Sequence[str]) -> VolumeParseResult

      Parse a sequence of volume definition into a tuple of three mappings - first one
      for all regular volumes, second one for volumes using secrets and third for disk
      volumes.

      :param ~typing.Sequence[str] env: Sequence of volumes specification. Each
                                        element can be either:
                                        - `STORAGE_URI:MOUNT_PATH:RW_FLAG`.
                                        - `SECRET_URI:MOUNT_PATH`.
                                        - `DISK_URI:MOUNT_PATH:RW_FLAG`.

      :return: :class:`VolumeParseResult` with parsing result


   .. method:: uri_to_str(uri: URL) -> str

      Convert :class:`~yarl.URL` object into :class:`str`.

   .. method:: str_to_uri(uri: str, *, allowed_schemes: Iterable[str] = (), \
                          cluster_name: Optional[str] = None, \
                          short: bool = False) -> URL

      Parse a string into *normalized* :class:`URL` for future usage by SDK methods.

      :param str uri: an URI (``'storage:folder/file.txt'``) or local file path
                      (``'/home/user/folder/file.txt'``) to parse.

      :param ~typing.Iterable[str] allowed_schemes: an *iterable* of accepted URI
                                                    schemes, e.g. ``('file',
                                                    'storage')``.  No scheme check is
                                                    performed by default.

      :param ~typing.Optional[str] cluster_name: optional cluster name, the default
                                                 cluster is used if not specified.

      :param bool short: if ``True``, return short URL
                         (without cluster and user names if possible).
                         ``False`` by default.

      :return: :class:`~yarl.URL` with parsed URI.

      :raise ValueError: if ``uri`` is invalid or provides a scheme not enumerated by
                         ``allowed_schemes`` argument.

   .. method:: uri_to_path(uri: URL, *, cluster_name: Optional[str] = None) -> Path

      Convert :class:`~yarl.URL` into :class:`~pathlib.Path`.

      :raise ValueError: if ``uri`` has no ``'file:'`` scheme.

   .. method:: path_to_uri(path: Path) -> URL

      Convert :class:`~pathlib.Path` object into *normalized* :class:`~yarl.URL` with
      ``'file:'`` scheme.

      :param ~pathlib.Path path: a path to convert.

      :return: :class:`~yarl.URL` that represent a ``path``.

   .. method:: normalize_uri(uri: URL, *, allowed_schemes: Iterable[str] = (), \
                          cluster_name: Optional[str] = None, \
                          short: bool = False) -> URL

      Normalize ``uri`` according to current user name, cluster and allowed schemes.

      *Normalized* form has two variants:

      1. Long form: cluster and user names are always present,
         e.g. `storage://cluster/user/dir/file.txt`.

      2. Short form: cluster and user are omitted if they are equal to default values
         given from `client.config.cluster_name` and `client.config.username`, e.g.
         `storage:dir/file.txt`.

      :param ~yarl.URL uri: an URI to normalize.

      :param ~typing.Iterable[str] allowed_schemes: an *iterable* of accepted URI
                                                    schemes, e.g. ``('file',
                                                    'storage')``.  No scheme check is
                                                    performed by default.

      :param ~typing.Optional[str] cluster_name: optional cluster name, the default
                                                 cluster is used if not specified.

      :param bool short: if ``True``, return short URL
                         (without cluster and user names if possible).
                         ``False`` by default.

      :return: :class:`~yarl.URL` with normalized URI.

      :raise ValueError: if ``uri`` is invalid or provides a scheme not enumerated by
                         ``allowed_schemes`` argument.

EnvParseResult
==============

.. class:: EnvParseResult

   .. attribute:: env

   Mapping of parsed environmental variables, :class:`~typing.Dict[str, str]`.

   .. attribute:: secret_env

   Mapping of parsed using secrets environmental variables, :class:`~typing.Dict[str, URL]`.


VolumeParseResult
=================

.. class:: VolumeParseResult

   .. attribute:: volumes

   List of parsed regular volumes, :class:`~typing.Sequence[str]`.

  .. attribute:: secret_files

   List of parsed secret files, :class:`~typing.List[SecretFile]`.

   .. attribute:: disk_volumes

   List of parsed disk volumes, :class:`~typing.List[DiskVolume]`.
