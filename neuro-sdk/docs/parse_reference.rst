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

      Parse a sequence of volume definition into a tuple of three mappings - first one for
      all regular volumes, second one for volumes using secrets and third for disk volumes.

      :param ~typing.Sequence[str] env: Sequence of volumes specification. Each
                                        element can be either:
                                        - `STORAGE_URI:MOUNT_PATH:RW_FLAG`.
                                        - `SECRET_URI:MOUNT_PATH`.
                                        - `DISK_URI:MOUNT_PATH:RW_FLAG`.

      :return: :class:`VolumeParseResult` with parsing result


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
