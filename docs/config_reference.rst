.. currentmodule:: neuromation.api


.. _config-reference:

===========================
Configuration API Reference
===========================


.. currentmodule:: neuromation.api


Config
======

.. class:: Config

   Configuration subsystem, available as :attr:`Client.config`.

   Use it for analyzing fetching information about the system configuration, e.g. a list
   of available clusters or switching the active cluster.

   .. attribute:: username

      User name used for working with Neuro Platform, read-only :class:`str`.

   .. attribute:: presets

      A :class:`typing.Mapping` of preset name (:class:`str`) to
      :class:`Preset` dataclass for the current cluster.

   .. attribute:: presets

      A :class:`typing.Mapping` of cluster name (:class:`str`) to
      :class:`Cluster` dataclass for available clusters.

   .. attribute:: cluster_name

      The current cluster name, read-only :class:`str`.

      To switch on another cluster use :meth:`switch_cluster`.

   .. comethod:: fetch() -> None

      Fetch available clusters configuration from the Neuro Platform.

      .. note::

         The call updates local configuration files.

   .. comethod:: switch_cluster(name: str) -> None

      Switch the current cluster to *name*.

      .. note::

         The call updates local configuration files.

   *Miscellaneous helpers*

   .. attribute:: api_url

      The Neuro Platform URL, :class:`yarl.URL`.

   .. attribute:: registry_url

      Docker Registry URL for the cluster, :class:`yarl.URL`.

      :attr:`Cluster.registry_url` for the current cluster.

   .. attribute:: storage_url

      Storage URL for the cluster, :class:`yarl.URL`.

      :attr:`Cluster.storage_url` for the current cluster.

   .. attribute:: monitoring_url

      Monitoring URL for the cluster, :class:`yarl.URL`.

      :attr:`Cluster.monitoring_url` for the current cluster.

   .. comethod:: get_user_config() -> Mapping[str, Any]

      Return user-provided config dictionary, run ``neuro help user-config`` for details
      about the user configuration files format and location.

      .. versionadded:: 20.01.15

   .. comethod:: token() -> str

      *Bearer* token to log into the Neuro Platform.

      The token expires after some period, the call automatically refreshes the token if
      needed.


Cluster
=======

.. class:: Cluster


   *Read-only* :class:`~dataclasses.dataclass` for describing a cluster configuration.

   Clusters are loaded on login to the Neuro platform and updated on
   :meth:`Config.fetch` call.

   :meth:`Config.switch_cluster` changes the active cluster.

   .. attribute:: name

      Cluster name, :class:`str`.

   .. attribute:: registry_url

      Docker Registry URL for the cluster, :class:`yarl.URL`.

   .. attribute:: storage_url

      Storage URL for the cluster, :class:`yarl.URL`.

   .. attribute:: users_url

      Users URL for the cluster, :class:`yarl.URL`.

   .. attribute:: monitoring_url

      Monitoring URL for the cluster, :class:`yarl.URL`.

   .. attribute:: presets

      A :class:`typing.Mapping` of available job resource presets, keys are preset names
      (:class:`str`), values are :class:`Preset` objects.


Preset
======

.. class:: Preset


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
