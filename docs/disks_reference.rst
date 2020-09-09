=====================
Disks API Reference
=====================


.. currentmodule:: neuromation.api


Disks
=====

.. class:: Disks

   Persistent disks subsystems. Disks can be passed as mounted volumes into a running job.

   .. comethod:: list() -> AsyncIterator[Disk]
      :async-for:

      List user's disks, async iterator. Yields :class:`Disk` instances.

   .. comethod:: create(storage: int) -> Disk

      Create a disk with capacity of *storage* bytes.

      :param int storage: storage capacity in bytes.

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

   .. attribute:: cluster

      Cluster disk resource belongs to, :class:`str`.

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
