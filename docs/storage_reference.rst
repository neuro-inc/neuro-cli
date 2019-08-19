=====================
Storage API Reference
=====================


.. currentmodule:: neuromation.api


Storage
=======


.. class:: Storage

   Storage subsystem.

   The subsystem can be used for listing remote storage, uploading and downloading files
   etc.


FileStatus
==========

.. class:: FileStatus

   *Read-only* :class:`~dataclasses.dataclass` for describing remote entry (file or
   directory).

   .. attribute:: path

      Path to the entry, :class:`str`.

   .. attribute:: size

      File size in bytes, :class:`int`.

   .. attribute:: type

      Entry type, :class:`FileStatusType` instance.

   .. attribute:: modification_time

      Modification time in seconds since the :ref:`epoch`, like the value returned from
      :func:`time.time()`.

   .. attribute:: permission

      Entrypoint permission, :class:`str`.
