.. _object-storage-reference:

============================
Object Storage API Reference
============================


.. currentmodule:: neuromation.api


Object Storage
==============

.. note::
   Be careful with using trailing slashes in Object Storage URL's, keys and prefixes.
   ``URL("object:my_bucket/folder/")`` is not the same as ``URL("object:my_bucket/folder")``. Try to always use trailing slash when working with folder prefixes or keys.
   Also note, that keys and prefixes are specified **without** a leading slash.


.. class:: ObjectStorage

   Object Storage interaction subsystem, available as :attr:`Client.object_storage`.

   The subsystem helps take advantage of many basic functionality of Object Storage
   solutions different cloud providers support. For AWS it would be S3, for GCP -
   Cloud Storage, etc.


   .. comethod:: list_buckets() -> List[BucketListing]

      List all buckets available to the current user. The availability is determined
      by Neuromation ACL definitions, so the bucket list may be different for each user.

      Permissions required:

      - ``object://{cluster_name}/`` *READ* - access to list all buckets
      - ``object://{cluster_name}/{bucket_name}/`` *READ* - access to list single
        bucket

      :return: a :class:`list` of :class:`BucketListing` objects available to user.

   .. comethod:: list_objects(bucket_name: str, prefix: str = "", \
                              recursive: bool = False, max_keys: int = 10000 \
                  ) -> List[Union[ObjectListing, PrefixListing]]

      List objects in the bucket. You can filter by prefix and return results similar
      to a folder structure if ``recursive=False`` is provided ::

         content = await client.object_storage.list_objects(
            bucket_name="my_bucket",
            recursive=False,
            prefix="parent/"
         )
         for obj in content:
            if isinstance(obj, ObjectListing):
               print("File ", obj.key)
            else:
               print("Folder ", obj.prefix)

      :param str bucket_name: Name of the bucket.
      :param str prefix: Filter results by a prefix in it's key.
      :param recursive bool: If ``True`` listing will contain *all* keys filtered by
          prefix, while with ``False`` only ones up to next ``/`` will be returned.
          To indicate missing keys, all that were listed will be combined under a
          common prefix and returned as :class:`PrefixListing`.
      :param max_keys int: Maximum number of :class:`ObjectListing` objects returned.

      :return: a :class:`list` of either :class:`ObjectListing` or
          :class:`PrefixListing` objects.

   .. comethod:: glob_objects(bucket_name: str, pattern: str) -> List[ObjectListing]

      Glob search the given key pattern *pattern* in the bucket *bucket_name*::

          for obj in await client.object_storage.glob_objects(
              bucket_name="my_bucket",
              pattern="folder1/**/*.txt"
          ):
              print(obj.key, obj.size, obj.modification_time)

      Similar to :meth:`Storage.glob` the ``“**”`` pattern means “this directory and
      all sub-directories, recursively”.

      :param str bucket_name: Name of the bucket.
      :param str pattern: key pattern according to the rules used by the Unix shell,
          similar to Python's :meth:`~glob.glob`.

      :return: a :class:`list` of either :class:`ObjectListing` objects.

   .. comethod:: head_object(bucket_name: str, key: str) -> ObjectListing

      Look up the object and return it's metadata.

      :param str bucket_name: Name of the bucket.
      :param str key: Key of the object.

      :return: :class:`ObjectListing` object.

      :raises: :exc:`FileNotFound` if key does not exist *or* you don't have access
          to it.

   .. comethod:: get_object(bucket_name: str, key: str) -> Object
      :async-with:

      Look up the object and return it's metadata with body content.

      :param str bucket_name: Name of the bucket.
      :param str key: Key of the object.

      :return: :class:`Object` object. Please note, that ``body_stream``'s lifetime is
         bounded to the asynchronous context manager. Accessing the attribute outside
         of the context manager will result in an error.

      :raises: :exc:`FileNotFound` if key does not exist *or* you don't have access
          to it.

   .. comethod:: fetch_object(bucket_name: str, key: str) -> AsyncIterator[bytes]
      :async-for:

      Look up the object and return it's body content only. The content will be streamed
      using an asynchronous iterator, e.g.::

         async for data in client.object_storage.fetch_object("my_bucket", key: "file.txt"):
             print("Next chunk of data:", data)

      :param str bucket_name: Name of the bucket.
      :param str key: Key of the object.

      :raises: :exc:`FileNotFound` if key does not exist *or* you don't have access
          to it.

   .. comethod:: put_object(bucket_name: str, key: str, \
            body: Union[AsyncIterator[bytes], bytes], \
            size: int, content_md5: str) -> str

      Create or replace object identified by ``key`` in the bucket, e.g::

         large_file = Path("large_file.dat")
         size = large_file.stat().st_size
         file_md5 = await calc_md5(large_file)

         async def body_stream():
             with large_file.open("r") as f:
                 for line in f:
                     yield f

         await client.object_storage.put_object(
             bucket_name="my_bucket", key="large_file.dat",
             body=body_stream, size=size, content_md5=file_md5
         )

      ``md5`` should be a Base64 encoding of the 128 bit digest, e.g::

            body = b"My file body"
            md5_digest = hashlib.md5(body).digest()
            encoded_md5 = base64.b64encode(md5_digest).decode()

      :param str bucket_name: Name of the bucket.
      :param str key: Key of the object.
      :param bytes body: Body of the object. Can be passed as either :class:`bytes`
         or as an ``AsyncIterator[bytes]``.
      :param int size: Size of body in bytes. Only required if body is passed as an
         ``AsyncIterator[bytes]``.
      :param str content_md5: Base64 encoded 128 bit MD5 digest of the body.

      :raises: :exc:`FileNotFound` if key does not exist *or* you don't have access
         to it.

   .. rubric:: Data transfer operations

   .. comethod:: make_url(bucket_name: str, key: str) -> URL:

      Minor helper function to make URL creation easier when using High Level
      operations like :meth:`ObjectStorage.download_dir`::

         src = URL("file:///usr/data")
         dst = client.object_storage.make_url(
            bucket_name="my_bucket",
            key="folder1/"
         )
         await client.object_storage.upload_dir(src, dst)

      :param ~yarl.URL src: path on remote storage to download a directory from
                            e.g. ``yarl.URL("storage:folder")``.

      :param ~yarl.URL dst: local path to save downloaded directory,
                            e.g. ``yarl.URL("file:///home/andrew/folder")``.

      :param AbstractRecursiveFileProgress progress:

         a callback interface for reporting downloading progress, ``None`` for no
         progress report (default).

   .. comethod:: download_dir(src: URL, dst: URL, \
                              *, progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Similarly to :meth:`Storage.download_dir`, allows to recursively download
      remote directory *src* to local path *dst*.

      :param ~yarl.URL src: path on Object Storage to download a directory from
                            e.g. ``yarl.URL("object:my_bucket/folder/")``.

      :param ~yarl.URL dst: local path to save downloaded directory,
                            e.g. ``yarl.URL("file:///home/andrew/folder")``.

      :param AbstractRecursiveFileProgress progress:

         a callback interface for reporting downloading progress, ``None`` for no
         progress report (default).

   .. comethod:: download_file(src: URL, dst: URL, \
                              *, progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Similarly to :meth:`Storage.download_file`, allows to download remote file
      *src* to local path *dst*.

      :param ~yarl.URL src: path on Object Storage to download a file from
                            e.g. ``yarl.URL("object:my_bucket/folder/file.bin")``.

      :param ~yarl.URL dst: local path to save downloaded file,
                            e.g. ``yarl.URL("file:///home/andrew/folder/file.bin")``.

      :param AbstractRecursiveFileProgress progress:

         a callback interface for reporting downloading progress, ``None`` for
         no progress report (default).

   .. comethod:: upload_dir(src: URL, dst: URL, \
                             *, progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Similarly to :meth:`Storage.upload_dir`, allows to recursively upload local
      directory *src* to Object Storage URL *dst*.


      :param ~yarl.URL src: path to uploaded directory on local disk,
                            e.g. ``yarl.URL("file:///home/andrew/folder")``.

      :param ~yarl.URL dst: path on Object Storage for saving uploading directory
                            e.g. ``yarl.URL("object:my_folder/folder/")``.

      :param AbstractRecursiveFileProgress progress:

         a callback interface for reporting uploading progress, ``None`` for no progress
         report (default).

   .. comethod:: upload_file(src: URL, dst: URL, \
                             *, progress: Optional[AbstractFileProgress] = None \
                 ) -> None:

      Similarly to :meth:`Storage.upload_file`, allows to upload local file *src* to
      storage URL *dst*.

      :param ~yarl.URL src: path to uploaded file on local disk,
                            e.g. ``yarl.URL("file:///home/andrew/folder/file.txt")``.

      :param ~yarl.URL dst: path on remote storage for saving uploading file
                            e.g. ``yarl.URL("storage:folder/file.txt")``.

      :param AbstractFileProgress progress:

         a callback interface for reporting uploading progress, ``None`` for no progress
         report (default).


BucketListing
=============

.. class:: BucketListing

   *Read-only* :class:`~dataclasses.dataclass` for describing bucket.

   .. attribute:: name

      Name of the bucket, :class:`str`.

   .. attribute:: creation_time

      Creation time in seconds since the :ref:`epoch`, like the value returned from
      :func:`time.time()`, :class:`int`.

   .. attribute:: permission

      Permission (*read*, *write* or *manage*), :class:`Action`. Derived from
      ACL permission action on ``object://{cluster_name}/{bucket_name}/`` resource.

   .. attribute:: uri

      Relative URI identifying the bucket, :class:`~yarl.URL`, e.g. ``object:my_bucket``


ObjectListing
=============

.. class:: ObjectListing

   *Read-only* :class:`~dataclasses.dataclass` for describing objects.

   .. attribute:: bucket_name

      Name of the bucket, :class:`str`.

   .. attribute:: key

      Key of the object, :class:`str`.

   .. attribute:: modification_time

      Modification time in seconds since the :ref:`epoch`, like the value returned from
      :func:`time.time()`, :class:`int`.

   .. attribute:: size

      Size of the data in *bytes*, :class:`int`.

   .. attribute:: uri

      Relative URI identifying the object, :class:`~yarl.URL`, e.g.
      ``object:my_bucket/file.txt``.

PrefixListing
=============

.. class:: ObjectListing

   *Read-only* :class:`~dataclasses.dataclass` for describing common prefixes for
   objects in non-recursive listing. You can treat it as a kind of *folder* on Object
   Storage.

   .. attribute:: bucket_name

      Name of the bucket, :class:`str`.

   .. attribute:: prefix

      Prefix path, :class:`str`.

   .. attribute:: uri

      Relative URI identifying the folder, :class:`~yarl.URL`, e.g.
      ``object:my_bucket/my_folder/``.

Object
======

.. class:: Object

   *Read-only* :class:`~dataclasses.dataclass` for describing common prefixes for
   objects in non-recursive listing. You can treat it as a kind of *folder* on Object
   Storage.

   .. attribute:: stats

      :class:`ObjectListing` related to the object.

   .. attribute:: body_stream

      :class:`aiohttp.StreamReader` content body.
