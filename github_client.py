import os
import subprocess
from pathlib import Path
from git import Repo


def _build_authenticated_url(url: str, token: str) -> str:
    if token is None:
        return url

    if url.startswith("https://"):
        _, remainder = url.split("https://", 1)
        return f"https://{token}@{remainder}"
    if url.startswith("http://"):
        _, remainder = url.split("http://", 1)
        return f"http://{token}@{remainder}"
    return url


def _run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )


def _normalize_sparse_pattern(ignore_dir: str) -> list[str]:
    path = ignore_dir.strip("/\\")
    if not path:
        return []
    return [f"!/{path}/", f"!/{path}/*", f"!/{path}/**"]


def clone_repo(
    url: str,
    token: str | None,
    destination: Path,
    ignore_dirs: list[str] | None = None,
    sparse_paths: list[str] | None = None,
) -> Path:
    authenticated_url = _build_authenticated_url(url, token)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        if os.name == "nt":
            _run_git([
                "-c",
                "core.longpaths=true",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                authenticated_url,
                str(destination),
            ])

            if sparse_paths or ignore_dirs:
                sparse_patterns: list[str] = []
                if sparse_paths:
                    sparse_patterns.extend(sparse_paths)
                else:
                    sparse_patterns.append("/*")

                if ignore_dirs:
                    for ignore_dir in ignore_dirs:
                        sparse_patterns.extend(_normalize_sparse_pattern(ignore_dir))

                _run_git(["sparse-checkout", "init", "--no-cone"], cwd=destination)
                _run_git(["sparse-checkout", "set"] + sparse_patterns, cwd=destination)

                if sparse_paths:
                    _run_git(["checkout", "HEAD"], cwd=destination)
            else:
                # No working tree checkout required when we only need the repository metadata.
                pass
        else:
            Repo.clone_from(authenticated_url, destination)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        stdout = exc.stdout.strip() if exc.stdout else ""
        raise RuntimeError(
            f"Git clone failed: {exc}\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}"
        ) from exc

    return destination
