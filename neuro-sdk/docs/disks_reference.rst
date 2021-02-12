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

   .. comethod:: create(  \
                        storage: int, \
                        life_span: typing.Optional[datetime.timedelta], \
                        name: typing.Optional[str], \
                 ) -> Disk

      Create a disk with capacity of *storage* bytes.

      :param int storage: storage capacity in bytes.

      :param ~typing.Optional[datetime.timedelta] life_span: Duration of no usage after which
                                                             disk will be deleted. ``None``
                                                             means no limit.

      :param ~typing.Optional[str] name: Name of the disk. Should be unique among all user's
                                         disk.

      :return: Newly created disk info (:class:`Disk`)

   .. comethod:: get(disk_id_or_name: str) -> Disk

      Get a disk with id or name *disk_id_or_name*.

      :param str disk_id_or_name: disk's id or name.

      :return: Disk info (:class:`Disk`)

   .. comethod:: rm(disk_id_or_name: str) -> None

      Delete a disk with id or name *disk_id_or_name*.

      :param str disk_id_or_name: disk's id or name.


Disk
=====

.. class:: Disk

   *Read-only* :class:`~dataclasses.dataclass` for describing persistent disk instance.

   .. attribute:: id

      The disk id, :class:`str`.

   .. attribute:: storage

      The disk capacity, in bytes, :class:`int`.

   .. attribute:: used_bytes

      The amount of used bytes on disk, :class:`int` or ``None`` if this
      information is not available. Note that this field is updated
      periodically, so it can contain incorrect data.

   .. attribute:: owner

      The disk owner username, :class:`str`.

   .. attribute:: name

      The disk name set by user, unique among all user's disks,
      :class:`str` or ``None`` if no name was set.

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

   .. attribute:: timeout_unused

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
