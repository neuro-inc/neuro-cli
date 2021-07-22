=====================
Secrets API Reference
=====================


.. currentmodule:: neuro_sdk


Secrets
=======

.. class:: Secrets

   Secured secrets subsystems.  Secrets can be passed as mounted files and environment
   variables into a running job.

   .. comethod:: list(cluster_name: Optional[str] = None) -> AsyncContextManager[AsyncIterator[Secret]]
      :async-with:
      :async-for:

      List user's secrets, async iterator. Yields :class:`Secret` instances.

      :param str cluster_name: cluster to list secrets. Default is current cluster.

   .. comethod:: add(key: str, value: bytes, cluster_name: Optional[str] = None) -> None

      Add a secret with name *key* and content *value*.

      :param str key: secret's name.

      :param bytes vale: secret's value.

      :param str cluster_name: cluster to create a secret. Default is current cluster.

   .. comethod:: rm(key: str, cluster_name: Optional[str] = None) -> None

      Delete a secret *key*.

      :param str key: secret's name.

      :param str cluster_name: cluster to look for a secret. Default is current cluster.
