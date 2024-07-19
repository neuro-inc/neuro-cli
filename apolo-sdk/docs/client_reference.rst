.. currentmodule:: apolo_sdk

Client class
============

.. class:: Client

   Apolo Platform client.

   For creating a client instance use :class:`Factory` or :func:`get`.

   The class provides access to Neu.ro subsystems like *jobs* or *storage*.

   .. attribute:: username

      User name used for working with Apolo Platform, read-only :class:`str`.

   .. attribute:: presets

      A :class:`typing.Mapping` of preset name (:class:`str`) to
      :class:`Preset` dataclass.

      Presets are loaded from server on login.

   .. attribute:: config

      Configuration subsystem, see :class:`Config` for details.

   .. attribute:: jobs

      Jobs subsystem, see :class:`Jobs` for details.

   .. attribute:: storage

      Storage subsystem, see :class:`Storage` for details.

   .. attribute:: users

      Users subsystem, see :class:`Users` for details.

   .. attribute:: images

      Images subsystem, see :class:`Images` for details.

   .. attribute:: secrets

      Images subsystem, see :class:`Secrets` for details.

   .. attribute:: disks

      Images subsystem, see :class:`Disks` for details.

   .. attribute:: parse

      A set or helpers used for parsing different Apolo API definitions, see
      :class:`Parser` for details.

   .. method:: close()
      :async:

      Close Apolo API client, all calls after closing are forbidden.

      The method is idempotent.

   .. attribute:: closed

      Is this client instance was closed, :class:`bool`.
