import asyncio
import subprocess

import aiohttp

from neuromation.clientv2 import ClientV2, JobDescription


def _validate_args_for_ssh_session(
    container_user: str, container_key: str, jump_host_key: str
) -> None:
    # Temporal solution - pending custom Jump Server with JWT support
    if not container_user:
        raise ValueError("Specify container user name")
    if not container_key:
        raise ValueError("Specify container RSA key path.")
    if not jump_host_key:
        raise ValueError(
            "Configure Github RSA key path." "See for more info `neuro config`."
        )


def _validate_job_status_for_ssh_session(job_status: JobDescription) -> None:
    if job_status.status == "running":
        if job_status.ssh:
            pass
        else:
            raise ValueError("Job should be started with SSH support.")
    else:
        raise ValueError(f"Job is not running. Job status is {job_status.status}")


def start_ssh(
    job_id: str,
    jump_host: str,
    jump_user: str,
    jump_key: str,
    container_user: str,
    container_key: str,
) -> None:
    nc_command = f"nc {job_id} 22"
    proxy_command = (
        f"ProxyCommand=ssh -i {jump_key} {jump_user}@{jump_host} {nc_command}"
    )
    try:
        subprocess.run(
            args=[
                "ssh",
                "-o",
                proxy_command,
                "-i",
                container_key,
                f"{container_user}@{job_id}",
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        # TODO (R Zubairov) check what ssh returns
        # on disconnect due to network issues.
        pass
    return None


async def _start_ssh_tunnel(
    job_status: JobDescription,
    jump_host: str,
    jump_user: str,
    jump_key: str,
    local_port: int,
) -> None:
    _validate_job_status_for_ssh_session(job_status)
    proc = await asyncio.create_subprocess_exec(
        "ssh",
        "-i",
        jump_key,
        f"{jump_user}@{jump_host}",
        "-f",
        "-N",
        "-L",
        f"{local_port}:{job_status.id}:22",
        stderr=subprocess.STDOUT,
    )
    await proc.wait()
    # TODO (ASvetlov) check ssh returncode
    # on disconnect due to network issues.


def _connect_ssh(
    username: str,
    job_status: JobDescription,
    jump_host_key: str,
    container_user: str,
    container_key: str,
) -> None:
    _validate_job_status_for_ssh_session(job_status)
    # We shall make an attempt to connect only in case it has SSH
    ssh_hostname = job_status.jump_host()
    if not ssh_hostname:
        raise RuntimeError("Job has no SSH server enabled")
    start_ssh(
        job_status.id,
        ssh_hostname,
        username,
        jump_host_key,
        container_user,
        container_key,
    )
    return None


async def connect_ssh(
    client: ClientV2,
    username: str,
    job_id: str,
    jump_host_key: str,
    container_user: str,
    container_key: str,
) -> None:
    _validate_args_for_ssh_session(container_user, container_key, jump_host_key)
    # Check if job is running
    try:
        job_status = await client.jobs.status(job_id)
    except aiohttp.ClientError as e:
        raise ValueError(f"Job not found. Job Id = {job_id}") from e
    _connect_ssh(username, job_status, jump_host_key, container_user, container_key)


async def remote_debug(
    client: ClientV2, username: str, job_id: str, jump_host_key: str, local_port: int
) -> None:
    if not jump_host_key:
        raise ValueError(
            "Configure Github RSA key path." "See for more info `neuro config`."
        )
    try:
        job_status = await client.jobs.status(job_id)
    except aiohttp.ClientError as e:
        raise ValueError(f"Job not found. Job Id = {job_id}") from e
    ssh_hostname = job_status.jump_host()
    if not ssh_hostname:
        raise RuntimeError("Job has no SSH server enabled")
    await _start_ssh_tunnel(
        job_status, ssh_hostname, username, jump_host_key, local_port
    )
