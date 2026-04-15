from __future__ import annotations

import os
import pathlib
from typing import Any

from .util import read_json


def runtime_dir(root: pathlib.Path, config: dict[str, Any]) -> pathlib.Path:
    return (root / config["runtime"]["localRuntimeDir"]).resolve()


def runtime_python_candidates(root: pathlib.Path, config: dict[str, Any]) -> list[pathlib.Path]:
    env_name = config["runtime"]["preferredPythonEnvVar"]
    candidates: list[pathlib.Path] = []
    env_value = os.environ.get(env_name)
    if env_value:
        candidates.append(pathlib.Path(env_value).expanduser().resolve())
    rdir = runtime_dir(root, config)
    candidates.append(rdir / "bin" / "python")
    candidates.append(rdir / "Scripts" / "python.exe")
    return candidates


def selected_runtime_python(root: pathlib.Path, config: dict[str, Any]) -> str | None:
    for candidate in runtime_python_candidates(root, config):
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def load_runtime_stamp(root: pathlib.Path, config: dict[str, Any]) -> dict[str, Any]:
    path = (root / config["runtime"]["runtimeStampPath"]).resolve()
    return read_json(path, default={}) or {}
