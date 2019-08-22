====================
Images API Reference
====================


.. currentmodule:: neuromation.api


Images
======

.. class:: Images

   Docker image subsystem.

   Used for pushing docker images onto Neuromation docker registry for later usage by
   :meth:`Jobs.run` and pulling these images back to local docker.

   .. comethod:: push(local: LocalImage, \
                      remote: Optional[RemoteImage] = None, \
                      *, \
                      progress: Optional[AbstractDockerImageProgress] = None, \
                 ) -> RemoteImage


      Push *local* docker image to *remote* side.

      :param LocalImage local: a spec of local docker image (e.g. created by ``docker
                               build``) for pushing on Neuromation registry.

      :param RemoteImage remote: a spec for remote image on Neuromation
                                 registry. Calculated from *local* image automatically
                                 if ``None`` (default).

      :param AbstractDockerImageProgress progress:

         a callback interface for reporting pushing progress, ``None`` for no progress
         report (default).

      :return: *remote* image if explicitly specified, calculated remote image if
               *remote* is ``None`` (:class:`RemoteImage`)


   .. comethod:: pull(remote: Optional[RemoteImage] = None, \
                      local: LocalImage, \
                      *, \
                      progress: Optional[AbstractDockerImageProgress] = None, \
                 ) -> RemoteImage


      Pull *remote* image from Neuromation registry to *local* docker side.

      :param RemoteImage remote: a spec for remote image on Neuromation
                                 registry.

      :param LocalImage local: a spec of local docker image to pull. Calculated from
                                 *remote* image automatically if ``None`` (default).


      :param AbstractDockerImageProgress progress:

         a callback interface for reporting pulling progress, ``None`` for no progress
         report (default).

      :return: *local* image if explicitly specified, calculated remote image if
               *local* is ``None`` (:class:`LocalImage`)


AbstractDockerImageProgress
===========================

.. class:: AbstractDockerImageProgress


LocalImage
==========

.. class:: LocalImage



RemoteImage
===========

.. class:: RemoteImage
