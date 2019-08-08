=========
Reference
=========


.. module:: neuromation.api


.. _client-instantiation:

Client instantiation
====================

.. function:: get()


Client
======

.. class:: Client

   Neuromation client.

   For creating a client instance use :class:`Factory` or :ref:`client-instantiation`.

   The class provides access to neuromation subsystems like *jobs* or *storage*.

   .. attribute:: username

      User name used for working with Neuromation platform, read-only :class:`str`.

   .. attribute:: jobs

      Jobs subsystem, see :class:`Jobs` for details.

   .. attribute:: storage

      Storage subsystem, see :class:`Storage` for details.

   .. attribute:: users

      Users subsystem, see :class:`Users` for details.

   .. attribute:: images

      Images subsystem, see :class:`Images` for details.

   .. attribute:: parse

      A set or helpers used for parsing different Neuromation API definitions, see
      :class:`Parser` for details.

   .. comethod:: close()

      Close Neuromation client, all calls after closing are forbidden.

      The method is idempotent.


Jobs
----

.. class:: Jobs

   Jobs subsystem.

   User can start new job, terminate it, get status, list running jobs etc.

   .. comethod:: run(container: Container, \
                     *, \
                     name: Optional[str] = None, \
                     description: Optional[str] = None, \
                     is_preemptible: bool = False, \
                     schedule_timeout: Optional[float] = None, \
                 ) -> JobDescription

      Start a new job.

      :param Container container: container description to start.

      :param str name: optional container name.

      :param str desciption: optional container description.

      :param bool is_preemtible: a flag that specifies is the job is *preemptible* or
                                 not, see :ref:`job-preemtibility` for details.

      :param float schedule_timeout: minimal timeout to wait before reporting that job
                                     cannot be scheduled because the lack of computation
                                     cluster resources (memory, CPU/GPU etc).

      :return JobDescription: dataclass with infomation about started job.


JobDescription
--------------

.. class:: JobDescription

   *Read-only* :class:`~dataclasses.dataclass` for describing a job.

   .. attribute:: id

      Job ID, :class:`str`.

   .. attribute:: owner

      A name of user who created a job, :class:`str`.

   .. attribute:: status

      Current status of job, :class:`JobStatus` enumeration.

   .. attribute:: history

      Additional information about job, e.g. creation time and process exit
      code. :class:`JobStatusHistory` instance.

   .. attribute:: container

      Description of container information used to start a job, :class:`Container`
      instance.

   .. attribute:: is_preemptible

      Is the job is *preemptible* or not, see :ref:`job-preemtibility` for details.

   .. attribute:: name

      Job name provided by user at creation time, :class:`str` or ``None`` if name is
      omitted.

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


Container
---------

.. class:: Container

   *Read-only* :class:`~dataclasses.dataclass` for describing Docker image and
   environment to run a job.

   .. attribute:: image

      :class:`RemoteImage` used for starting a contatiner.

   .. attribute:: resources

      :class:`Resources` which are used to schedule a container.

   .. attribute:: entrypoint

      Docker ENTRYPOINT_ used for overriding image entypoint (:class:`str`), default
      ``None`` is used to pick entrypoint from image's *Dockerfile*.

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


Resources
---------

.. class:: Resources

   *Read-only* :class:`~dataclasses.dataclass` for describing resources (memory, CPU/GPU
   etc.) availiable for container, see also :attr:`Container.resources` attribute.

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


.. _ENTRYPOINT: https://docs.docker.com/engine/reference/builder/#entrypoint

.. _CMD: https://docs.docker.com/engine/reference/builder/#cmd
