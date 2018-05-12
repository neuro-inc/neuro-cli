import pytest
from dataclasses import replace

from neuromation import JobStatus, Resources

JOB_ARGS = {
    'resources': Resources(memory='64M', cpu=1, gpu=1),
    'image': 'test/image',
    'dataset': 'storage://~/dataset',
    'results': 'storage://~/results'
}

JOB_TIMEOUT_SEC = 0.05


def train_or_infer_value_errors(func, args):
    with pytest.raises(TypeError):
        func()

    with pytest.raises(ValueError, match=r'Invalid image path: .*'):
        func(**{**args, 'image': 'invalid  image path'})

    with pytest.raises(ValueError, match=r'Invalid resource request: .*'):
        func(**{**args, 'resources': None})

    with pytest.raises(ValueError, match=r'Invalid resource request: .*'):
        func(**{**args, 'resources': Resources(memory='foo', cpu=1, gpu=1)})

    with pytest.raises(ValueError, match=r'Invalid resource request: .*'):
        func(**{**args, 'resources': Resources(memory='64M', cpu=-1, gpu=1)})

    with pytest.raises(ValueError, match=r'Invalid resource request: .*'):
        func(**{**args, 'resources': Resources(memory='64M', cpu=1, gpu=-1)})

    with pytest.raises(ValueError, match=r'Invalid uri: .*'):
        func(**{**args, 'dataset': 'bad-uri'})

    with pytest.raises(ValueError, match=r'Invalid uri: .*'):
        func(**{**args, 'results': 'bad-uri'})


@pytest.mark.parametrize(
    'job,cmd,model_uri',
    [
        ('train', 'bash -c "echo foo"', None),
        ('infer', 'bash -c "echo foo"', 'storage://~/model'),
        ('infer', 'bash -c "echo foo"', 'storage://~/model'),
        ('train', ['bash', '-c', 'echo foo'], None),
        ('infer', ['bash', '-c', 'echo foo'], 'storage://~/model'),
        ('infer', ['bash', '-c', 'echo foo'], 'storage://~/model')

    ])
def test_job(job, cmd, model_uri, model):
    args = JOB_ARGS if model_uri is None else {**JOB_ARGS, 'model': model_uri}
    func = getattr(model, job)
    job_status = func(**args)
    assert replace(job_status, id=None) == JobStatus(
            results=JOB_ARGS['results'],
            status='RUNNING',
            id=None
        )

    with pytest.raises(TimeoutError):
        job_status.wait(timeout=JOB_TIMEOUT_SEC)

    status = job_status.wait()

    assert replace(status, id=None) == JobStatus(
        results=JOB_ARGS['results'],
        status='FINISHED',
        id=None
    )


def test_train_errors(model):
    train_or_infer_value_errors(model.train, JOB_ARGS)


def test_infer_errors(model):
    args = {**JOB_ARGS, 'model': 'storage://~/model'}
    train_or_infer_value_errors(model.infer, args)

    with pytest.raises(ValueError, match=r'Invalid uri: .*'):
        model.infer({**args, 'model': 'bad-uri'})
