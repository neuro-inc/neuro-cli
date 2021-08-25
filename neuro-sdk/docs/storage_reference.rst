.. _storage-reference:

=====================
Storage API Reference
=====================


.. currentmodule:: neuro_sdk


Storage
=======


.. class:: Storage

   Storage subsystem, available as :attr:`Client.storage`.

   The subsystem can be used for listing remote storage, uploading and downloading files
   etc.


   .. rubric:: Remote filesystem operations

   .. comethod:: glob(uri: URL, *, dironly: bool = False) -> AsyncContextManager[AsyncIterator[URL]]
      :async-with:
      :async-for:

      Glob the given relative pattern *uri* in the directory represented by this *uri*,
      yielding all matching remote files (of any kind)::

          folder = yarl.URL("storage:folder/*")
          async with client.storage.glob(folder) as uris:
              async for uri in uris:
                  print(uri)

      The ``“**”`` pattern means “this directory and all sub-directories,
      recursively”. In other words, it enables recursive globbing::

          folder = yarl.URL("storage:folder/**/*.py")
          async with client.storage.glob(folder) as uris:
              async for uri in uris:
                  print(uri)

      :param ~yarl.URL uri: a pattern to glob.

      :param bool fironly: search in directory names only, ``False`` by default.

      :return: asynchronous iterator that can be used for enumerating found files and
               directories.

   .. comethod:: list(uri: URL) -> AsyncContextManager[AsyncIterator[FileStatus]]
      :async-with:
      :async-for:

      List a directory *uri* on the storage, e.g.::

         folder = yarl.URL("storage:folder")
         async with client.storage.list(folder) as statuses:
             async for status in statuses:
                 print(status.name, status.size)

      :param ~yarl.URL uri: directory to list

      :return: asynchronous iterator which emits :class:`FileStatus` objects
               for the directory content.

   .. comethod:: mkdir(uri: URL, *, parents: bool = False, \
                       exist_ok: bool = False \
                 ) -> None

      Create a directory *uri*. Also create parent directories if *parents* is ``True``,
      fail if directory exists and not *exist_ok*.

      :param ~yarl.URL uri: a path to directory for creation,
                            e.g. ``yarl.URL("storage:folder/subfolder")``.

      :param bool parents: create parent directories if they are not exists, raise
                           :exc:`FileNotFound` otherwise (``False`` by default).


      :param bool exist_ok: finish successfully if directory *uri* already exists, raise
                            :exc:`FileExistsError` otherwise (``False`` by default).


      :raises: :exc:`FileExistsError` if requested directory already exists and
               *exist_ok* flag is not set.

      :raises: :exc:`FileNotFound` if parent directories don't exist and *parents* flag
               is not set.

   .. comethod:: mv(src: URL, dst: URL) -> None

      Rename remote file or directory *src* to *dst*.

      :param ~yarl.URL src: remote source path,
                            e.g. ``yarl.URL("storage:folder/file.bin")``.

      :param ~yarl.URL dst: remote destination path,
                            e.g. ``yarl.URL("storage:folder/new.bin")``.


   .. comethod:: rm(uri: URL, *, recursive: bool = False) -> None

      Remove remote file or directory *uri*.

      :param ~yarl.URL uri: remote path to delete,
                            e.g. ``yarl.URL("storage:folder/file.bin")``.

      :param bool recursive: remove a directory recursively with all nested files and
                             folders if ``True`` (``False`` by default).

      :raises: :exc:`IsADirectoryError` if *uri* points on a directory and *recursive*
               flag is not set.

   .. comethod:: stat(uri: URL) -> FileStatus

      Return information about *uri*.

      :param ~yarl.URL uri: storage path for requested info, e.g.
                            ``yarl.URL("storage:folder/file.bin")``.

      :return: data structure for given *uri*, :class:`FileStatus` object.

   .. comethod:: disk_usage(cluster_name: Optional[str] = None) -> DiskUsageInfo

      Return information about disk usage in given cluster.

      :param str cluster_name: cluster name to retrieve info. If ``None`` current
                               cluster will be used.

      :return: data structure for given cluster, :class:`DiskUsageInfo` object.

   .. rubric:: File operations

   .. comethod:: create(uri: URL, data: AsyncIterator[bytes]) -> None

      Create a file on storage under *uri* name, file it with a content from *data*
      asynchronous iterator, e.g.::

         async def gen():
             for i in range(10):
                 yield str(i) * 10

         file = yarl.URL("storage:folder/file.bin")
         source = gen()
         await client.storage.create(file, source)
         await source.aclose()

      :param ~yarl.URL uri: path to created file,
                            e.g. ``yarl.URL("storage:folder/file.txt")``.

      :param ~typing.AsyncIterator[bytes] data: asynchronous iterator used as data
                                                provider for file content.

   .. comethod:: write(uri: URL, data: bytes, offset: int) -> None

      Overwrite the part of existing file on storage under *uri* name.

      :param ~yarl.URL uri: storage path of remote file, e.g.
                            ``yarl.URL("storage:folder/file.txt")``.

      :param bytes data: data to be written. Must be non-empty.

      :param int offset: position in file from which to write.

   .. comethod:: open(uri: URL, offset: int = 0, size: Optional[int] = None) -> AsyncContextManager[AsyncIterator[bytes]]
      :async-with:
      :async-for:

      Get the content of remote file *uri* or its fragment as asynchronous iterator, e.g.::

         file = yarl.URL("storage:folder/file.txt")
         async with client.storage.open(file) as content:
             async for data in content:
                 print(data)

      :param ~yarl.URL uri: storage path of remote file, e.g.
                            ``yarl.URL("storage:folder/file.txt")``.

      :param int offset: Position in file from which to read.

      :param int size: Maximal size of the read data.  If ``None`` read to the end of the file.

      :return: asynchronous iterator used for retrieving the file content.

   .. rubric:: Copy operations

   .. comethod:: download_dir(src: URL, dst: URL, \
                              *, update: bool = False, \
                              continue_: bool = False, \
                              filter: Optional[Callable[[str], Awaitable[bool]]] = None, \
                              progress: Optional[AbstractRecursiveFileProgress] = None \
                 ) -> None:

      Recursively download remote directory *src* to local path *dst*.

      :param ~yarl.URL src: path on remote storage to download a directory from
                            e.g. ``yarl.URL("storage:folder")``.

      :param ~yarl.URL dst: local path to save downloaded directory,
                            e.g. ``yarl.URL("file:///home/andrew/folder")``.

      :param bool update: if true, download only when the source file is newer
                          than the destination file or when the destination
                          file is missing.

      :param bool continue_: if true, download only the part of the source file
                             past the end of the destination file and append it
                             to the destination file if the destination file is
                             newer and not longer than the source file.
                             Otherwise download and overwrite the whole file.

      :param Callable[[str], Awaitable[bool]] filter:

         a callback function for determining which files and subdirectories
         be downloaded. It is called with a relative path of file or directory
         and if the result is false the file or directory will be skipped.

      :param AbstractRecursiveFileProgress progress:

         a callback interface for reporting downloading progress, ``None`` for no
         progress report (default).

   .. comethod:: download_file(src: URL, dst: URL, \
                               *, update: bool = False, \
                               continue_: bool = False, \
                               progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Download remote file *src* to local path *dst*.

      :param ~yarl.URL src: path on remote storage to download a file from
                            e.g. ``yarl.URL("storage:folder/file.bin")``.

      :param ~yarl.URL dst: local path to save downloaded file,
                            e.g. ``yarl.URL("file:///home/andrew/folder/file.bin")``.

      :param bool update: if true, download only when the source file is newer
                          than the destination file or when the destination
                          file is missing.

      :param bool continue_: if true, download only the part of the source file
                             past the end of the destination file and append it
                             to the destination file if the destination file is
                             newer and not longer than the source file.
                             Otherwise download and overwrite the whole file.

      :param AbstractFileProgress progress:

         a callback interface for reporting downloading progress, ``None`` for
         no progress report (default).

   .. comethod:: upload_dir(src: URL, dst: URL, \
                            *, update: bool = False, \
                            continue_: bool = False, \
                            filter: Optional[Callable[[str], Awaitable[bool]]] = None, \
                            ignore_file_names: AbstractSet[str] = frozenset(), \
                            progress: Optional[AbstractRecursiveFileProgress] = None \
                 ) -> None:

      Recursively upload local directory *src* to storage URL *dst*.

      :param ~yarl.URL src: path to uploaded directory on local disk,
                            e.g. ``yarl.URL("file:///home/andrew/folder")``.

      :param ~yarl.URL dst: path on remote storage for saving uploading directory
                            e.g. ``yarl.URL("storage:folder")``.

      :param bool update: if true, download only when the source file is newer
                          than the destination file or when the destination
                          file is missing.

      :param bool continue_: if true, upload only the part of the source file
                             past the end of the destination file and append it
                             to the destination file if the destination file is
                             newer and not longer than the source file.
                             Otherwise upload and overwrite the whole file.

      :param Callable[[str], Awaitable[bool]] filter:

         a callback function for determining which files and subdirectories
         be uploaded. It is called with a relative path of file or directory
         and if the result is false the file or directory will be skipped.

      :param AbstractSet[str] ignore_file_names:

         a set of names of files which specify filters for skipping files and
         subdirectories. The format of ignore files is the same as
         ``.gitignore``.

      :param AbstractRecursiveFileProgress progress:

         a callback interface for reporting uploading progress, ``None`` for no progress
         report (default).

   .. comethod:: upload_file(src: URL, dst: URL, \
                             *, update: bool = False, \
                             continue_: bool = False, \
                             progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Upload local file *src* to storage URL *dst*.

      :param ~yarl.URL src: path to uploaded file on local disk,
                            e.g. ``yarl.URL("file:///home/andrew/folder/file.txt")``.

      :param ~yarl.URL dst: path on remote storage for saving uploading file
                            e.g. ``yarl.URL("storage:folder/file.txt")``.

      :param bool update: if true, download only when the source file is newer
                          than the destination file or when the destination
                          file is missing.

      :param bool continue_: if true, upload only the part of the source file
                             past the end of the destination file and append it
                             to the destination file if the destination file is
                             newer and not longer than the source file.
                             Otherwise upload and overwrite the whole file.

      :param AbstractFileProgress progress:

         a callback interface for reporting uploading progress, ``None`` for no progress
         report (default).

FileStatus
==========

.. class:: FileStatus

   *Read-only* :class:`~dataclasses.dataclass` for describing remote entry (file or
   directory).

   .. attribute:: modification_time

      Modification time in seconds since the :ref:`epoch`, like the value returned from
      :func:`time.time()`.

   .. attribute:: name

      File or directory name, the last part of :attr:`path`.

   .. attribute:: permission

      Permission (*read*, *write* or *manage*), :class:`Action`.

   .. attribute:: path

      Path to the entry, :class:`str`.

   .. attribute:: size

      File size in bytes, :class:`int`.

   .. attribute:: type

      Entry type, :class:`FileStatusType` instance.

   .. method:: is_file() -> bool

      ``True`` if :attr:`type` is :attr:`FileStatusType.FILE`

   .. method:: is_dir() -> bool

      ``True`` if :attr:`type` is :attr:`FileStatusType.DIRECTORY`


AbstractFileProgress
====================

.. class:: AbstractFileProgress

   Base class for file upload/download progress, inherited from :class:`abc.ABC`.  User
   should inherit from this class and override abstract methods to get progress info
   from :meth:`Storage.upload_file` and :meth:`Storage.download_file` calls.

   .. method:: start(data: StorageProgressStart) -> None

      Called when transmission of the file starts.

      :param StorageProgressStart data: data for this event

   .. method:: step(data: StorageProgressStep) -> None

      Called when transmission of the file progresses (more bytes are transmitted).

      :param StorageProgressStep data: data for this event

   .. method:: complete(data: StorageProgressComplete) -> None

      Called when transmission of the file completes.

      :param StorageProgressComplete data: data for this event


AbstractRecursiveFileProgress
=============================

.. class:: AbstractRecursiveFileProgress

   Base class for recursive file upload/download progress, inherited from
   :class:`AbstractFileProgress`.  User should inherit from this class and override
   abstract methods to get progress info from :meth:`Storage.upload_dir` and
   :meth:`Storage.download_dir` calls.

   .. method:: enter(data: StorageProgressEnterDir) -> None

      Called when recursive process enters directory.

      :param StorageProgressComplete data: data for this event

   .. method:: leave(data: StorageProgressLeaveDir) -> None

      Called when recursive process leaves directory. All files in that
      directory are now transmitted.

      :param StorageProgressLeaveDir data: data for this event

   .. method:: fail(data: StorageProgressFail) -> None

      Called when recursive process fails. It can happen because of
      touching special file (like block device file) or some other
      reason. Check **data.message** to get error details.

      :param StorageProgressFail data: data for this event


AbstractDeleteProgress
======================

.. class:: AbstractDeleteProgress

   Base class for file/directory delete progress, inherited from :class:`abc.ABC`.  User
   should inherit from this class and override abstract methods to get progress info
   from :meth:`Storage.rm` calls.

  .. method:: delete(data: StorageProgressDelete) -> None

      Called when single item (either file or directory) was deleted. Directory removal
      happens after removal of all files and subdirectories is contains.

      :param StorageProgressDelete data: data for this event


StorageProgress event classes
=============================

.. class:: StorageProgressStart

   .. attribute:: src

      :class:`yarl.URL` of source file, e.g. ``URL("file:/home/user/upload.txt")``.

   .. attribute:: dst

      :class:`yarl.URL` of destination file, e.g. ``URL("storage://cluster/user/upload_to.txt")``.

   .. attribute:: size

      Size of the transmitted file, in bytes, :class:`int`.

.. class:: StorageProgressStep

   .. attribute:: src

      :class:`yarl.URL` of source file, e.g. ``URL("file:/home/user/upload.txt")``.

   .. attribute:: dst

      :class:`yarl.URL` of destination file, e.g. ``URL("storage://cluster/user/upload_to.txt")``.

   .. attribute:: current

      Count of the transmitted bytes, :class:`int`.

   .. attribute:: size

      Size of the transmitted file, in bytes, :class:`int`.

.. class:: StorageProgressComplete

   .. attribute:: src

      :class:`yarl.URL` of source file, e.g. ``URL("file:/home/user/upload.txt")``.

   .. attribute:: dst

      :class:`yarl.URL` of destination file, e.g. ``URL("storage://cluster/user/upload_to.txt")``.

   .. attribute:: size

      Size of the transmitted file, in bytes, :class:`int`.

.. class:: StorageProgressEnterDir

   .. attribute:: src

      :class:`yarl.URL` of source directory, e.g. ``URL("file:/home/user/upload/")``.

   .. attribute:: dst

      :class:`yarl.URL` of destination directory, e.g. ``URL("storage://cluster/user/upload_to/")``.

.. class:: StorageProgressLeaveDir

   .. attribute:: src

      :class:`yarl.URL` of source directory, e.g. ``URL("file:/home/user/upload/")``.

   .. attribute:: dst

      :class:`yarl.URL` of destination directory, e.g. ``URL("storage://cluster/user/upload_to/")``.

.. class:: StorageProgressFail

   .. attribute:: src

      :class:`yarl.URL` of source file that triggered error, e.g. ``URL("file:/dev/sda")``.

   .. attribute:: dst

      :class:`yarl.URL` of destination file, e.g. ``URL("storage://cluster/user/dev/sda.bin")``.

   .. attribute:: message

      Explanation message for the error, :class:`str`.

.. class:: StorageProgressDelete

   .. attribute:: uri

      :class:`yarl.URL` of the deleted file, e.g. ``URL("storage://cluster/user/delete_me.txt")``.

   .. attribute:: is_dir

      **True** if removed item was a directory; **False** otherwise. :class:`bool`


DiskUsageInfo
=============

.. class:: DiskUsageInfo

   *Read-only* :class:`~dataclasses.dataclass` for describing disk usage in particular
   cluster

   .. attribute:: cluster_name

      Name of cluster, :class:`str`.

   .. attribute:: total

      Total storage size in bytes, :class:`int`.

   .. attribute:: used

      Used storage size in bytes, :class:`int`.

   .. attribute:: free

      Free storage size in bytes, :class:`int`.
