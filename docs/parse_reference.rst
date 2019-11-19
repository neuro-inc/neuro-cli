================
Parser Reference
================


.. currentmodule:: neuromation.api


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
