"""Install this repository's skills into a coding agent's skills directory."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ai-skills")
except PackageNotFoundError:
    __version__ = "unknown"
