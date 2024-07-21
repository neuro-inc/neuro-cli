.. apolo-sdk documentation master file, created by
   sphinx-quickstart on Tue Aug  6 11:38:43 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

====================
Apolo SDK for Python
====================

A Python library for the Apolo Platform API.

Installation
============

The latest stable release is available on PyPI_. Either add ``apolo-sdk`` to your
``requirements.txt`` or install with pip::

   $ pip install -U apolo-sdk


Getting Started
===============


To start working with the Apolo Platform you need to login first.  The easiest way
to do it is the using of :term:`CLI` utility::

   $ apolo login

After the login a configuration file is created and it can be read later.

Use :func:`apolo_sdk.get` for initializing client instance from existing
configuration file::

  import apolo_sdk

  async with apolo_sdk.get() as client:
      async with client.jobs.list() as job_iter:
          jobs = [job async for job in job_iter]


The example above instantiates a ``client`` object in *async context manager* and
fetches a list of user's jobs.  On exit from ``async with`` statement the ``client``
object is closed and is not available for future calls.


See :ref:`usage` section for ideas how typical operations can be done with Apolo
platform. :ref:`reference` section contains the full API reference for all API classes,
functions etc.

Contents
========

.. toctree::
   :maxdepth: 2

   usage
   reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _PyPI: https://pypi.org/project/apolo-sdk/
