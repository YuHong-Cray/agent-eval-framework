"""Docker container lifecycle management."""

import dataclasses
from pathlib import Path
from typing import Optional

import docker

from eval_framework.config import config


@dataclasses.dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class SandboxManager:
    """Manages Docker sandbox lifecycle for test execution."""

    def __init__(self):
        cfg = config.get_sandbox_config()
        self._client = None  # lazy init
        self._built_images: set[str] = set()
        self._network_mode = cfg.get("network_mode", "none")
        self._default_timeout = cfg.get("timeout_default", 900)

    def _get_client(self):
        """Lazy-initialize Docker client."""
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def build_image(self, name: str, dockerfile_path: Path) -> str:
        """Build a sandbox Docker image. Returns the image tag."""
        tag = f"eval-sandbox-{name}:latest"
        context_dir = dockerfile_path.parent
        self._get_client().images.build(
            path=str(context_dir),
            dockerfile=dockerfile_path.name,
            tag=tag,
            rm=True,
        )
        self._built_images.add(name)
        return tag

    def is_image_built(self, name: str) -> bool:
        return name in self._built_images

    def run(
        self,
        image: str,
        command: str,
        volume_mounts: dict[str, str],
        timeout: Optional[int] = None,
        env_vars: Optional[dict[str, str]] = None,
    ) -> SandboxResult:
        """Run a command inside a sandbox container and return results."""
        timeout = timeout or self._default_timeout
        tag = f"eval-sandbox-{image}:latest"

        volumes = {}
        binds = {}
        for host_path, container_path in volume_mounts.items():
            abs_host = str(Path(host_path).resolve())
            volumes[container_path] = {"bind": abs_host, "mode": "rw"}
            binds[abs_host] = {"bind": container_path, "mode": "rw"}

        try:
            container = self._get_client().containers.run(
                image=tag,
                command=command,
                volumes=volumes,
                environment=env_vars or {},
                network_mode=self._network_mode,
                detach=True,
                remove=False,
            )
            result = container.wait(timeout=timeout)
            logs = container.logs(stdout=True, stderr=True)
            container.remove(force=True)

            return SandboxResult(
                exit_code=result["StatusCode"],
                stdout=logs.decode("utf-8", errors="replace"),
                stderr="",
            )
        except docker.errors.NotFound:
            raise RuntimeError(f"Image '{tag}' not found. Build it first.")
        except Exception as e:
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                return SandboxResult(
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    timed_out=True,
                )
            raise
