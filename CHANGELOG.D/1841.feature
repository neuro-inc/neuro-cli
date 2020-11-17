Added option `--continue` for command `neuro cp`.
It specified, copy only the part of the source file
past the end of the destination file and append it
to the destination file if the destination file is
newer and not longer than the source file.
Otherwise copy the whole file.
Added corresponding keyword-only boolean parameter `continue_` to the API.
