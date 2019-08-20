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

   .. comethod:: glob(uri: URL, *, dironly: bool = False) -> AsyncIterator[URL]
      :async-for:

      Glob the given relative pattern *uri* in the directory represented by this path,
      yielding all matching files (of any kind)::

          async for url in client.storage.glob(yarl.URL("storage:folder/*")):
              print(url)

      The ``“**”`` pattern means “this directory and all subdirectories,
      recursively”. In other words, it enables recursive globbing::

          async for url in client.storage.glob(yarl.URL("storage:folder/**/*.py")):
              print(url)

      :param ~yarl.URL uri: a pattern to glob.

      :param bool fironly: search in directory names only, ``False`` by default.

      :return: asynchronous iterator that can be used for enumerating found files and
               directories.

   .. comethod:: ls(uri: URL) -> List[FileStatus)

      List a directory *uri* on the storage, e.g.::

         content = await client.storage.ls(yarl.URL("storage:folder"))

      :param ~yarl.URL uri: directory to list

      :return: a :class:`list` or :class:`FileStatus` objects with the directory
               contents.

   .. comethod:: mkdirs(uri: URL, *, parents: bool = False, \
                        exist_ok: bool = False
                 ) -> None

      Create a dirctory *uri*. Also create parent directories if *parents* is ``True``,
      fail if directory exists and not *exist_ok*.

      :param ~yarl.URL uri: a path to directory for creation,
                            e.g. ``yarl.URL("storage:folder/subfolder")``.

      :param bool parents: create parent directories if they are not exists, raise
                           :exc:`FileNotFound` otherwise (``False`` by default).


      :param bool exist_ok: finish successfully if directory *uri* already exists, raise
                            :exc:`FileExistsError` otherwise (``False by default).


      :raises: :exc:`FileExistsError` if requested directory already exists and
               *exist_ok* flag is not set.

      :raises: :exc:`FileNotFound` if parent directories dont exist and *parents* flag
               is not set.


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
