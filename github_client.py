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


def clone_repo(url: str, token: str | None, destination: Path) -> Path:
    authenticated_url = _build_authenticated_url(url, token)
    Repo.clone_from(authenticated_url, destination)
    return destination
