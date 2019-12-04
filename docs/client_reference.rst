.. currentmodule:: neuromation.api

Client class
============

.. class:: Client

   Neuro Platform client.

   For creating a client instance use :class:`Factory` or :func:`get`.

   The class provides access to neuromation subsystems like *jobs* or *storage*.

   .. attribute:: username

      User name used for working with Neuro Platform, read-only :class:`str`.

   .. attribute:: presets

      A :class:`~coleections.abc.Mapping` of preset name (:class:`str`) to
      :class:`Preset` dataclass.

      Presets are loaded from server on login.

   .. attribute:: jobs

      Jobs subsystem, see :class:`Jobs` for details.

   .. attribute:: storage

      Storage subsystem, see :class:`Storage` for details.

   .. attribute:: users

      Users subsystem, see :class:`Users` for details.

   .. attribute:: images

      Images subsystem, see :class:`Images` for details.

   .. attribute:: parse

      A set or helpers used for parsing different Neuro API definitions, see
      :class:`Parser` for details.

   .. comethod:: close()

      Close Neuro API client, all calls after closing are forbidden.

      The method is idempotent.


Preset
======

   *Read-only* :class:`~dataclasses.dataclass` for describing a job configuration
   provided by Neuro Platform.

   Presets list is loaded on login to the Neuro platform and depends on used
   cluster.

   .. attribute:: cpu

      Requested number of CPUs, :class:`float`. Please note, Docker supports fractions
      here, e.g. ``0.5`` CPU means a half or CPU on the target node.

   .. attribute:: memory_mb

      Requested memory amount in MegaBytes, :class:`int`.

   .. attribute:: is_preemptible

      A flag that specifies is the job is *preemptible* or not, see :ref:`Preemption
      <job-preemption>` for details.

   .. attribute:: gpu

      The number of requested GPUs, :class:`int`. Use ``None`` for jobs that doesn't
      require GPU.

   .. attribute:: gpu_model

      The name of requested GPU model, :class:`str` (or ``None`` for job without GPUs).

   .. attribute:: tpu_type

      Requested TPU type, see also https://en.wikipedia.org/wiki/Tensor_processing_unit

   .. attribute:: tpu_software_version

      Requested TPU software version.
