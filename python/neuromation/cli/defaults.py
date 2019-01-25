from .rc import Config


DEFAULTS = {
    "token": None,
    "api_url": Config.url,
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


GPU_MODELS = ["nvidia-tesla-k80", "nvidia-tesla-p4", "nvidia-tesla-v100"]
