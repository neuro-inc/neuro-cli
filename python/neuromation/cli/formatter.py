class OutputFormatter:

    from neuromation.client.jobs import JobItem

    @classmethod
    def format_job(cls, job: JobItem, quiet: bool=True):
        if quiet:
            return job.id
        return f'Job ID: {job.id} Status: {job.status}\n' + \
               f'Shortcuts:\n' + \
               f'  neuro job status {job.id}  # check job status\n' + \
               f'  neuro job monitor {job.id} # monitor job stdout\n' + \
               f'  neuro job kill {job.id}    # kill job'
