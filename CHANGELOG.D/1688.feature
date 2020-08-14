Make JobStatus calculation forward-compatible; `JobStatus.UNKNOWN` is returned for
unknown statuses but the code doesn't raise `ValueError` at least.