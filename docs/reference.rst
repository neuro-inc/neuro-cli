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

      : URL = URL()
    http_url_named: URL = URL()
    ssh_server: URL = URL()
    internal_hostname: Optional[str] = None



.. class:: Container

   *Frozen* dataclass
