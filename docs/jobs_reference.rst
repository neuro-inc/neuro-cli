.. _jobs-reference:

==================
Jobs API Reference
==================


.. currentmodule:: neuromation.api


Jobs
====

.. class:: Jobs

   Jobs subsystem, available as :attr:`Client.jobs`.

   User can start new job, terminate it, get status, list running jobs etc.

   .. comethod:: exec(id: str, cmd: List[str], *, \
                      tty: bool = False, \
                      timeout: Optional[float] = None, \
                 ) -> int

      Execute a command in a running job, wait for the command finish.

      :param str id: job :attr:`~JobDescription.id` to use for command execution.

      :param ~typing.Iterable[str] cmd: the command to execute, a sequence of
                                        :class:`str`, e.g. :class:`list` of strings.

      :param bool tty: ``True`` if :term:`tty` mode is requested, default is
                       ``False``.

      :param float timeout: maximum time in seconds to wait for the command execution
                            finish, infinite if ``None`` (default).

      :return: Executed process exit code (:class:`int`), zero for successful execution.

   .. comethod:: kill(id: str) -> None

      Kill a job.

      :param str id: job :attr:`~JobDescription.id` to kill.

   .. comethod:: list(*, statuses: Iterable[JobStatus] = (), \
                      name: str = "" \
                      tags: Sequence[str] = (), \
                      owners: Iterable[str] = (),
                 ) -> List[JobDescription]

      List user jobs, all scheduled, running and finished jobs by default.

      :param ~typing.Iterable[JobStatus] statuses: filter jobs by their statuses.

                                                   The parameter can be a set or list of
                                                   requested statuses,
                                                   e.g. ``{JobStatus.PENDIND,
                                                   JobStatus.RUNNING}`` can be used for
                                                   requesting only scheduled and running
                                                   job but skip finished and failed
                                                   ones.

                                                   Empty sequence means that jobs with
                                                   all statuses are returned (default
                                                   behavior). The list can be pretty
                                                   huge though.

      :param str name: Filter jobs by :attr:`~JobDescription.name` (exact match).

                       Empty string means that no filter is applied (default).

      :param str name: Filter jobs by :attr:`~JobDescription.tags`. Retrieves all
                       jobs submitted with at least one tag from the specified list.

                       Empty list means that no filter is applied (default).

      :param ~typing.Iterable[str] owners: filter jobs by their owners.

                                           The parameter can be a set or list of owner
                                           usernames (see :attr:`JobDescription.owner`
                                           for details).

                                           No owners filter is applied if the iterable
                                           is empty.

      :return: a :class:`list` of :class:`JobDescription` objects.


   .. comethod:: monitor(id: str) -> AsyncIterator[bytes]
      :async-for:

      Get job logs as a sequence of data chunks, e.g.::

         async for chunk in client.jobs.monitor(job_id):
             print(chunk.encode('utf8', errors='replace')

      :param str id: job :attr:`~JobDescription.id` to retrieve logs.

      :return: :class:`~collections.abc.AsyncIterator` over :class:`bytes` log chunks.


   .. comethod:: port_forward(id: str, local_port: int, job_port: int, *, \
                              no_key_check: bool = False \
                 ) -> None
      :async-with:

      Forward local port to job, e.g.::

         async with client.jobs.port_forward(job_id, 8080, 80):
             # port forwarding is awailable inside with-block

      :param str id: job :attr:`~JobDescription.id`.

      :param int local_port: local TCP port to forward.

      :param int jot_port: remote TCP port in a job to forward.

   .. comethod:: run(container: Container, \
                     *, \
                     name: Optional[str] = None, \
                     tags: Sequence[str] = (), \
                     description: Optional[str] = None, \
                     is_preemptible: bool = False, \
                     schedule_timeout: Optional[float] = None, \
                     life_span: Optional[float] = None, \
                 ) -> JobDescription

      Start a new job.

      :param Container container: container description to start.

      :param str name: optional container name.

      :param str name: optional job tags.

      :param str desciption: optional container description.

      :param bool is_preemtible: a flag that specifies is the job is *preemptible* or
                                 not, see :ref:`Preemption <job-preemption>` for
                                 details.

      :param float schedule_timeout: minimal timeout to wait before reporting that job
                                     cannot be scheduled because the lack of computation
                                     cluster resources (memory, CPU/GPU etc).

      :param float life_span: job run-time limit in seconds. Pass `None` to disable.

      :return: :class:`JobDescription` instance with information about started job.

   .. comethod:: status(id: str) -> JobDescription

      Get information about a job.

      :param str id: job :attr:`~JobDescription.id` to get its status.

      :return: :class:`JobDescription` instance with job status details.

   .. comethod:: tags() -> List[str]

      Get the list of all tags submitted by the user.

      :return: :class:`List[str]` list of tags.

   .. comethod:: top(id: str) -> AsyncIterator[JobTelemetry]
      :async-for:

      Get job usage statistics, e.g.::

          async for data in client.jobs.top(job_id):
              print(data.cpu, data.memory)

      :param str id: job :attr:`~JobDescription.id` to get telemetry data.

      :return: asynchronous iterator which emits `JobTelemetry` objects periodically.


Container
=========

.. class:: Container

   *Read-only* :class:`~dataclasses.dataclass` for describing Docker image and
   environment to run a job.

   .. attribute:: image

      :class:`RemoteImage` used for starting a container.

   .. attribute:: resources

      :class:`Resources` which are used to schedule a container.

   .. attribute:: entrypoint

      Docker ENTRYPOINT_ used for overriding image entry-point (:class:`str`), default
      ``None`` is used to pick entry-point from image's *Dockerfile*.

   .. attribute:: command

      Command line to execute inside a container (:class:`str`), ``None`` for picking
      command line from image's *Dockerfile*.

   .. attribute:: http

      :class:`HTTPPort` for describing parameters of HTTP server exposed by container,
      ``None`` if the container doesn't provide HTTP access.

   .. attribute:: env

      Custom *environment variables* for pushing into container's task.

      A :class:`~collections.abc.Mapping` where keys are environments variables names
      and values are variable values, both :class:`str`. Empty :class:`dict` by default.

   .. attribute:: volumes

      Docker volumes to mount into container, a :class:`~collections.abc.Sequence` or
      :class:`Volume` objects. Empty :class:`list` by default.


HTTPPort
========

.. class:: HTTPPort

   *Read-only* :class:`~dataclasses.dataclass` for exposing HTTP server started in a
   job.

   To access this server from remote machine please use :attr:`JobDescription.http_url`.

   .. attribute:: port

      Open port number in container's port namespace, :class:`int`.

   .. attribute:: requires_auth

      Authentication in Neuro Platform is required for access to exposed HTTP
      server if ``True``, the port is open publicly otherwise.


JobDescription
==============

.. class:: JobDescription

   *Read-only* :class:`~dataclasses.dataclass` for describing a job.

   .. attribute:: id

      Job ID, :class:`str`.

   .. attribute:: owner

      A name of user who created a job, :class:`str`.

   .. attribute:: cluster_name

      A name of cluster where job was scheduled, :class:`str`.

      .. versionadded:: 19.9.11

   .. attribute:: status

      Current status of job, :class:`JobStatus` enumeration.

   .. attribute:: history

      Additional information about job, e.g. creation time and process exit
      code. :class:`JobStatusHistory` instance.

   .. attribute:: container

      Description of container information used to start a job, :class:`Container`
      instance.

   .. attribute:: is_preemptible

      Is the job is *preemptible* or not, see :ref:`Preemption <job-preemption>` for
      details.

   .. attribute:: name

      Job name provided by user at creation time, :class:`str` or ``None`` if name is
      omitted.

   .. attribute:: tags

      List of job tags provided by user at creation time, :class:`Sequence[str]` or
      ``()`` if tags omitted.

   .. attribute:: description

      Job description text provided by user at creation time, :class:`str` or ``None``
      if description is omitted.

   .. attribute:: http_url

      :class:`yarl.URL` for HTTP server exposed by job, empty URL if the job doesn't
      expose HTTP server.

   .. attribute:: ssh_server

      :class:`yarl.URL` to access running job by SSH. Internal field, don't access it
      from custom code. Use :meth:`Jobs.exec` and :meth:`Jobs.port_forward` as
      official API for accessing to running job.


   .. attribute:: internal_hostname

      DNS name to access the running job from other jobs.


JobStatus
=========

.. class:: JobStatus

   *Enumeration* that describes job state.

   Can be one of the following statues:

   .. attribute:: PENDING

      Job is scheduled for execution but not started yet.

   .. attribute:: RUNNING

      Job is running now.

   .. attribute:: SUCCEEDED

      Job is finished successfully.

   .. attribute:: FAILED

      Job execution is failed.

   .. attribute:: UNKNOWN

      Invalid (or unknown) status code, should be never returned from server.


JobStatusHistory
================

.. class:: JobStatusHistory

   *Read-only* :class:`~dataclasses.dataclass` for describing job status details,
   e.g. creation and finishing time, exit code etc.

   .. attribute:: status

      Current status of job, :class:`JobStatus` enumeration.

      The same as :attr:`JobDescription.status`.

   .. attribute:: reason

      Additional information for current status, :class:`str`.

      Examples of *reason* values:

      * ``'ContainerCreating'`` for :attr:`JobStatus.PENDING` job that initiates a pod
        for container.

      * ``'ErrImagePull'`` for :attr:`JobStatus.FAILED` job that cannot pull specified
        image.

   .. attribute:: description

      Extended description for short abbreviation described by :attr:`reason`,
      empty :class:`str` if no additional information is provided.

   .. attribute:: exit_code

      Exit code for container's process (:class:`int`) or ``None`` if the job was not
      started or is still running.

   .. attribute:: created_at

      Job creation timestamp, :class:`~datetime.datetime` or ``None``.

   .. attribute:: started_at

      Job starting timestamp, :class:`~datetime.datetime` or ``None`` if job not
      started.

   .. attribute:: finished_at

      Job finishing timestamp, :class:`~datetime.datetime` or ``None`` if job not
      finished.


JobTelemetry
============

.. class:: JobTelemetry

   *Read-only* :class:`~dataclasses.dataclass` for job telemetry (statistics),
   e.g. consumed CPU load, memory footprint etc.

   .. seealso:: :meth:`Jobs.top`.

   .. attribute:: timestamp

      Date and time of telemetry report (:class:`float`), time in seconds since the
      :ref:`epoch`, like the value returned from :func:`time.time()`.

      See :mod:`time` and :mod:`datetime` for more information how to handle the
      timestamp.

   .. attribute:: cpu

      CPU load, :class:`float`. ``1`` means fully loaded one CPU unit, ``0.5`` is for
      half-utilized CPU.

   .. attribute:: memory

      Consumed memory in megabytes, :class:`float`.

   .. attribute:: gpu_duty_cycle

      Percentage of time over the past sample period (10 seconds) during which the
      accelerator was actively processing. :class:`int` between ``1`` and ``100``,
      ``None`` if the job has no GPU available.

   .. attribute:: gpu_memory

      Percentage of used GPU memory, :class:`float` between ``0`` and ``1``.


Resources
=========

.. class:: Resources

   *Read-only* :class:`~dataclasses.dataclass` for describing resources (memory, CPU/GPU
   etc.) available for container, see also :attr:`Container.resources` attribute.

   .. attribute:: memory_mb

      Requested memory amount in MegaBytes, :class:`int`.

   .. attribute:: cpu

      Requested number of CPUs, :class:`float`. Please note, Docker supports fractions
      here, e.g. ``0.5`` CPU means a half or CPU on the target node.

   .. attribute:: gpu

      The number of requested GPUs, :class:`int`. Use ``None`` for jobs that doesn't
      require GPU.

   .. attribute:: gpu_model

      The name of requested GPU model, :class:`str` (or ``None`` for job without GPUs).

   .. attribute:: shm

      Use Linux shared memory or not, :class:`bool`. Provide ``True`` if you don't know
      what ``/dev/shm`` device means.

   .. attribute:: tpu_type

      Requested TPU type, see also https://en.wikipedia.org/wiki/Tensor_processing_unit

   .. attribute:: tpu_software_version

      Requested TPU software version.


Volume
======


.. class:: Volume


   *Read-only* :class:`~dataclasses.dataclass` for describing mounted volumes of a
   container.

   .. attribute:: storage_uri

      An URL on remotes storage, :class:`yarl.URL`.

   .. attribute:: container_path

      A path on container filesystem, :class:`str`.

   .. attribute:: read_only

      ``True`` is the volume is mounted in read-only mode, ``False`` for read-write
      (default).


.. _ENTRYPOINT: https://docs.docker.com/engine/reference/builder/#entrypoint

.. _CMD: https://docs.docker.com/engine/reference/builder/#cmd
