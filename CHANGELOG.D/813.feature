`neuro storage cp` now supports copying to/from non-regular files like character devices and named pipes. In particular this allows to output the file to the stdout or get the input from the stdin::

    neuro storage cp storage://~/file.txt /dev/stdout
    neuro storage cp /dev/stdin storage://~/file.txt
