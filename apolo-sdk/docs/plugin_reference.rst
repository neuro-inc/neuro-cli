.. currentmodule:: neuro_sdk


.. _plugin-reference:

===========================
Plugins API Reference
===========================


.. currentmodule:: neuro_sdk


PluginManager
=============

.. class:: PluginManager

   Allows plugins to register their features. Provided to **neuro_api** entrypoint (check
   https://packaging.python.org/specifications/entry-points/ for more info about entry points).

   .. attribute:: config

      Define new user config parameters :class:`ConfigBuilder`.


ConfigBuilder
=============

.. class:: ConfigBuilder

   Helper class that contains methods to define new user config variables
   (check  :meth:`Config.get_user_config`).

   .. method:: define_int(section: str, name: str) -> None

      Define new integer config parameter with given name in given section

   .. method:: define_bool(section: str, name: str) -> None

      Define new `bool` config parameter with given name in given section

   .. method:: define_float(section: str, name: str) -> None

      Define new float config parameter with given name in given section

   .. method:: define_str(section: str, name: str) -> None

      Define new string config parameter with given name in given section

   .. method:: define_int_list(section: str, name: str) -> None

      Define new integer list config parameter with given name in given section

   .. method:: define_bool_list(section: str, name: str) -> None

      Define new `bool` list config parameter with given name in given section

   .. method:: define_str_list(section: str, name: str) -> None

      Define new string list config parameter with given name in given section

   .. method:: define_float_list(section: str, name: str) -> None

      Define new float list config parameter with given name in given section
