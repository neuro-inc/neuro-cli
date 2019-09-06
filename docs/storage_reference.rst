.. _storage-reference:

=====================
Storage API Reference
=====================


.. currentmodule:: neuromation.api


Storage
=======


.. class:: Storage

   Storage subsystem, available as :attr:`Client.storage`.

   The subsystem can be used for listing remote storage, uploading and downloading files
   etc.


   .. rubric:: Remote filesystem operations

   .. comethod:: glob(uri: URL, *, dironly: bool = False) -> AsyncIterator[URL]
      :async-for:

      Glob the given relative pattern *uri* in the directory represented by this *uri*,
      yielding all matching remote files (of any kind)::

          folder = yarl.URL("storage:folder/*")
          async for url in client.storage.glob(folder):
              print(url)

      The ``“**”`` pattern means “this directory and all sub-directories,
      recursively”. In other words, it enables recursive globbing::

          folder = yarl.URL("storage:folder/**/*.py")
          async for url in client.storage.glob(folder):
              print(url)

      :param ~yarl.URL uri: a pattern to glob.

      :param bool fironly: search in directory names only, ``False`` by default.

      :return: asynchronous iterator that can be used for enumerating found files and
               directories.

   .. comethod:: ls(uri: URL) -> List[FileStatus)

      List a directory *uri* on the storage, e.g.::

         folder = yarl.URL("storage:folder")
         content = await client.storage.ls(folder)

      :param ~yarl.URL uri: directory to list

      :return: a :class:`list` or :class:`FileStatus` objects with the directory
               contents.

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


   .. rubric:: File operations

   .. comethod:: create(uri: URL, data: AsyncIterator[bytes]) -> None

      Create a file on storage under *uri* name, file it with a content from *data*
      asynchronous iterator, e.g.::

         async def gen():
             for i in range(10):
                 yield str(i) * 10

         file = yarl.URL("storage:folder/file.bin")
         await client.storage.create(file, gen())

      :param ~yarl.URL uri: path to created file,
                            e.g. ``yarl.URL("storage:folder/file.txt")``.

      :param ~typing.AsyncIterator[bytes] data: asynchronous iterator used as data
                                                provider for file content.

   .. comethod:: open(uri: URL) -> AsyncIterator[bytes]
      :async-for:

      Get the content of remove file *uri* as asynchronous iterator, e.g.::

         file = yarl.URL("storage:folder/file.txt")
         async for data in client.storage.open(file):
             print(data)

   .. rubric:: Copy operations

   .. comethod:: download_dir(src: URL, dst: URL, \
                              *, progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Recursively download remote directory *src* to local path *dst*.

      :param ~yarl.URL src: path on remote storage to download a directory from
                            e.g. ``yarl.URL("storage:folder")``.

      :param ~yarl.URL dst: local path to save downloaded directory,
                            e.g. ``yarl.URL("file:///home/andrew/folder")``.

      :param AbstractRecursiveFileProgress progress:

         a callback interface for reporting downloading progress, ``None`` for no
         progress report (default).

   .. comethod:: download_file(src: URL, dst: URL, \
                              *, progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Download remote file *src* to local path *dst*.

      :param ~yarl.URL src: path on remote storage to download a file from
                            e.g. ``yarl.URL("storage:folder/file.bin")``.

      :param ~yarl.URL dst: local path to save downloaded file,
                            e.g. ``yarl.URL("file:///home/andrew/folder/file.bin")``.

      :param AbstractRecursiveFileProgress progress:

         a callback interface for reporting downloading progress, ``None`` for
         no progress report (default).

   .. comethod:: upload_dir(src: URL, dst: URL, \
                             *, progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Recursively upload local directory *src* to storage URL *dst*.

      :param ~yarl.URL src: path to uploaded directory on local disk,
                            e.g. ``yarl.URL("file:///home/andrew/folder")``.

      :param ~yarl.URL dst: path on remote storage for saving uploading directory
                            e.g. ``yarl.URL("storage:folder")``.

      :param AbstractRecursiveFileProgress progress:

         a callback interface for reporting uploading progress, ``None`` for no progress
         report (default).

   .. comethod:: upload_file(src: URL, dst: URL, \
                             *, progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Upload local file *src* to storage URL *dst*.

      :param ~yarl.URL src: path to uploaded file on local disk,
                            e.g. ``yarl.URL("file:///home/andrew/folder/file.txt")``.

      :param ~yarl.URL dst: path on remote storage for saving uploading file
                            e.g. ``yarl.URL("storage:folder/file.txt")``.

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


.. class:: AbstractRecursiveFileProgress

   Base class for file upload/download progress, inherited from
   :class:`AbstractFileProgress`.  User should inherit from this class and override
   abstract methods to get progress info from :meth:`Storage.upload_dir` and
   :meth:`Storage.download_dir` calls.
