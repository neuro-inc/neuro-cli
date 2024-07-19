=============================
ServiceAccounts API Reference
=============================


.. currentmodule:: apolo_sdk


ServiceAccounts
===============

.. class:: ServiceAccounts

   Service accounts subsystems. Service accounts can be used to generate tokens that can be
   used in automated environments by third-party services.

   .. method:: list() -> AsyncContextManager[AsyncIterator[ServiceAccount]]
      :async:

      List user's service accounts, async iterator. Yields :class:`ServiceAccount` instances.

   .. method:: create(  \
                        name: typing.Optional[str], \
                        default_cluster: typing.Optional[str], \
                 ) -> typing.Tuple[ServiceAccount, str]
      :async:

      Create a service account.

      :param str role: Authorization role to use for this service account.

      :param ~typing.Optional[str] default_cluster: Default cluster to embed into generated token. Defaults
                                                    to current cluster.

      :return: Pair of newly created service account info and token. This is the only way to
               get token of a service account.

   .. method:: get(id_or_name: str) -> ServiceAccount
      :async:

      Get a service account with id or name *id_or_name*.

      :param str id_or_name: service account's id or name.

      :return: Service account info (:class:`ServiceAccount`)

   .. method:: rm(id_or_name: str) -> None
      :async:

      Revoke and delete a service account with id or name *id_or_name*.

      :param str id_or_name: service account's id or name.


ServiceAccount
==============

.. class:: ServiceAccount

   *Read-only* :class:`~dataclasses.dataclass` for describing service account instance.

   .. attribute:: id

      The service account id, :class:`str`.

   .. attribute:: role

      Authorization role this service account is based on.

   .. attribute:: owner

      The service account owner username, :class:`str`.

   .. attribute:: name

      The service account name set by user, unique among all user's service accounts,
      :class:`str` or ``None`` if no name was set.

   .. attribute:: default_cluster

      A default cluster that this service account uses after login, :class:`str`.

   .. attribute:: created_at

      Service account creation timestamp, :class:`~datetime.datetime`.

   .. attribute:: role_deleted

      ``True`` if corresponding role was deleted, otherwise ``False``.
