from .rc import ConfigFactory


def load_defaults():
    return {
        "token": None,
        "api_url": ConfigFactory.load().url,
        "username": "username",
        "model_train_gpu_number": 0,
        "model_train_gpu_model": "nvidia-tesla-k80",
        "model_train_cpu_number": 0.1,
        "model_train_memory_amount": "1G",
        "model_debug_local_port": 31234,
        "job_submit_gpu_number": 0,
        "job_submit_gpu_model": "nvidia-tesla-k80",
        "job_submit_cpu_number": 0.1,
        "job_submit_memory_amount": "1G",
        "job_ssh_user": "root",
    }


DEFAULTS = load_defaults()

GPU_MODELS = ["nvidia-tesla-k80", "nvidia-tesla-p4", "nvidia-tesla-v100"]
