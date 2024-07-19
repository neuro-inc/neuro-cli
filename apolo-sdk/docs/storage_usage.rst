.. currentmodule:: aplo_sdk

.. _storage-usage:

=============
Storage Usage
=============


Use Storage API (available as :attr:`Client.storage`) for uploading files to the
Apolo Storage and downloading them back.  This chapter describes several common
scenarios like uploading / downloading directories recursively.

There are many methods in :class:`Storage` namespace, here we describe a few.

Blob Storage API (available as :attr:`Client.blob_storage`) is another subsystem,
which has a similar Upload/Download interface as methods shown below. Please refer to
:class:`BlobStorage` documentation for more details.


Upload a Folder
===============


Use :meth:`Storage.upload_dir` to upload a local directory on the Apolo Storage::

   from apolo_sdk import get
   from yarl import URL

   async with get() as client:
       await client.storage.upload_dir(
           URL("file:local_folder"),
           URL("storage:remote_folder"),
       )

The example above recursively uploads all files and directories ``./local_folder`` to
``storage://<username>/remote_folder``.

Use ``update=True`` flag to upload only files that are newer than are present on the
Storage::

   await client.storage.upload_dir(
       URL("file:local_folder"),
       URL("storage:remote_folder"),
       update=True,
   )

Download a Folder
=================

Use :meth:`Storage.download_dir` for downloading data from the Apolo Storage to
local disk.

The method is a counterpart to :meth:`Storage.upload_dir` and has the same arguments::

   await client.storage.download_dir(
       URL("storage:remote_folder"),
       URL("file:local_folder"),
   )

The example above recursively downloads files and directories from
``storage:remote_folder`` to ``./local_folder``.
