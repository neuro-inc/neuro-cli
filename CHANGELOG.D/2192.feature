All asynchronous iterators returned by API support now an asynchronous manager protocol. It is strongly preferable to use "asyn with" before iterating them. For example::

          async with client.jobs.list() as jobs:
              async for job in jobs:
                  print(job.id)
