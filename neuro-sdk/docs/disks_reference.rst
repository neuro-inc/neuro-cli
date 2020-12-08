=====================
Disks API Reference
=====================


.. currentmodule:: neuro_sdk


Disks
=====

.. class:: Disks

   Persistent disks subsystems. Disks can be passed as mounted volumes into a running job.

   .. comethod:: list() -> AsyncIterator[Disk]
      :async-for:

      List user's disks, async iterator. Yields :class:`Disk` instances.

   .. comethod:: create(storage: int, life_span: typing.Optional[datetime.timedelta]) -> Disk

      Create a disk with capacity of *storage* bytes.

      :param int storage: storage capacity in bytes.

      :param ~typing.Optional[datetime.timedelta] life_span: Duration of no usage after which
                                                             disk will be deleted. ``None``
                                                             means no limit.

      :return: Newly created disk info (:class:`Disk`)

   .. comethod:: get(disk_id: str) -> Disk

      Get a disk with id *disk_id*.

      :param str disk_id: disk's id.

      :return: Disk info (:class:`Disk`)

   .. comethod:: rm(disk_id: str) -> None

      Delete a disk with id *disk_id*.

      :param str disk_id: disk's id.


Disk
=====

.. class:: Disk

   *Read-only* :class:`~dataclasses.dataclass` for describing persistent disk instance.

   .. attribute:: id

      The disk id, :class:`str`.

   .. attribute:: storage

      The disk capacity, in bytes, :class:`int`.

   .. attribute:: owner

      The disk owner username, :class:`str`.

   .. attribute:: status

      Current disk status, :class:`Disk.Status`.

   .. attribute:: uri

      URI of the disk resource, :class:`yarl.URL`.

   .. attribute:: cluster_name

      Cluster disk resource belongs to, :class:`str`.

   .. attribute:: created_at

      Disk creation timestamp, :class:`~datetime.datetime`.

   .. attribute:: last_usage

      Timestamp when disk was last attached to job, :class:`~datetime.datetime`
      or ``None`` if disk was never used.

   .. attribute:: life_span

      Max unused duration after which disk will be deleted by platform,
      :class:`~datetime.timedelta` or ``None`` if there is no limit.


Disk.Status
===========

.. class:: Disk.Status

   *Enumeration* that describes disk status.

   Can be one of the following values:

   .. attribute:: PENDING

      Disk is still creating. It can be attached to job, but job will not start
      until disk is created.

   .. attribute:: READY

      Disk is created and ready to use.

   .. attribute:: BROKEN

      Disk is broken and cannot be used anymore. Can happen if underneath storage
      device was destroyed.
