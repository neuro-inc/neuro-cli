=====================
Buckets API Reference
=====================


.. currentmodule:: neuro_sdk


Buckets
=======

.. class:: Buckets

   Blob storage buckets subsystems.

   .. comethod:: list(cluster_name: Optional[str] = None) -> AsyncContextManager[AsyncIterator[Bucket]]
      :async-for:

      List user's buckets, async iterator. Yields :class:`Bucket` instances.

      :param str cluster_name: cluster to list buckets. Default is current cluster.

   .. comethod:: create(  \
                        name: typing.Optional[str], \
                        cluster_name: Optional[str] = None, \
                 ) -> Bucket

      Create a new bucket.

      :param ~typing.Optional[str] name: Name of the bucket. Should be unique among all user's
                                         bucket.

      :param str cluster_name: cluster to create a bucket. Default is current cluster.


      :return: Newly created bucket info (:class:`Bucket`)

   .. comethod:: get(bucket_id_or_name: str, cluster_name: Optional[str] = None) -> Bucket

      Get a bucket with id or name *bucket_id_or_name*.

      :param str bucket_id_or_name: bucket's id or name.

      :param str cluster_name: cluster to look for a bucket. Default is current cluster.

      :return: Bucket info (:class:`Bucket`)

   .. comethod:: rm(bucket_id_or_name: str, cluster_name: Optional[str] = None) -> None

      Delete a bucket with id or name *bucket_id_or_name*.

      :param str bucket_id_or_name: bucket's id or name.

      :param str cluster_name: cluster to look for a bucket. Default is current cluster.


Bucket
======

.. class:: Bucket

   *Read-only* :class:`~dataclasses.dataclass` for describing single bucket.

   .. attribute:: id

      The bucket id, :class:`str`.

   .. attribute:: owner

      The bucket owner username, :class:`str`.

   .. attribute:: name

      The bucket name set by user, unique among all user's buckets,
      :class:`str` or ``None`` if no name was set.

   .. attribute:: uri

      URI of the bucket resource, :class:`yarl.URL`.

   .. attribute:: cluster_name

      Cluster this bucket belongs to, :class:`str`.

   .. attribute:: created_at

      Bucket creation timestamp, :class:`~datetime.datetime`.

   .. attribute:: provider

      Blob storage provider this bucket belongs to, :class:`Bucket.Provider`.

   .. attribute:: credentials

      Credentials to access a bucket inside the provider, :class:`Mapping[str, str]`


Bucket.Provider
===============

.. class:: Bucket.Provider

   *Enumeration* that describes bucket providers.

   Can be one of the following values:

   .. attribute:: AWS

      Amazon Web Services S3 bucket
