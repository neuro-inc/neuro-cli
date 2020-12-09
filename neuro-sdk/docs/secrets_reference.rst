=====================
Secrets API Reference
=====================


.. currentmodule:: neuro_sdk


Secrets
=======

.. class:: Secrets

   Secured secrets subsystems.  Secrets can be passed as mounted files and environment
   variables into a running job.

   .. comethod:: list() -> AsyncIterator[Secret]
      :async-for:

      List user's secrets, async iterator. Yields :class:`Secret` instances.

   .. comethod:: add(key: str, value: bytes) -> None

      Add a secret with name *key* and content *value*.

      :param str key: secret's name.

      :param bytes vale: secret's value.

   .. comethod:: rm(key: str) -> None

      Delete a secret *key*.

      :param str key: secret's name.
