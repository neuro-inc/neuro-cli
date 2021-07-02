.. neuro-sdk documentation master file, created by
   sphinx-quickstart on Tue Aug  6 11:38:43 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

====================
Neuro SDK for Python
====================

A Python library for the Neuro Platform API.

Installation
============

The latest stable release is available on PyPI_. Either add ``neuro-sdk`` to your
``requirements.txt`` or install with pip::

   $ pip install -U neuro-sdk


Getting Started
===============


To start working with the Neuro Platform you need to login first.  The easiest way
to do it is the using of :term:`CLI` utility::

   $ neuro login

After the login a configuration file is created and it can be read later.

Use :func:`neuro_sdk.get` for initializing client instance from existing
configuration file::

  import neuro_sdk

  async with neuro_sdk.get() as client:
      async with client.jobs.list() as job_iter:
          jobs = [job async for job in job_iter]


The example above instantiates a ``client`` object in *async context manager* and
fetches a list of user's jobs.  On exit from ``async with`` statement the ``client``
object is closed and is not available for future calls.


See :ref:`usage` section for ideas how typical operations can be done with Neu.ro
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


.. _PyPI: https://pypi.org/project/neuro-sdk/
