from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


SUPPORTED_EXTENSIONS = {".yaml", ".yml", ".json"}


class ConfigLoadError(Exception):
    """Raised when a configuration file cannot be loaded."""


def load_config(config_path: str | Path) -> Dict[str, Any]:
    """Load a YAML or JSON config file into a Python dictionary.

    Parameters
    ----------
    config_path:
        Path to a .yaml, .yml, or .json configuration file.

    Returns
    -------
    dict
        Parsed configuration dictionary.

    Raises
    ------
    ConfigLoadError
        If the file does not exist, has an unsupported extension, or cannot be parsed.
    """
    path = Path(config_path).expanduser().resolve()
    print(path)
    if not path.exists():
        raise ConfigLoadError(f"Config file not found: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ConfigLoadError(
            f"Unsupported config format: {path.suffix}. "
            f"Expected one of: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            if yaml is None:
                raise ConfigLoadError(
                    "PyYAML is required to load YAML files. Install it with `pip install pyyaml`."
                )
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
    except Exception as exc:
        raise ConfigLoadError(f"Failed to parse config file {path}: {exc}") from exc

    if data is None:
        raise ConfigLoadError(f"Config file is empty: {path}")

    if not isinstance(data, dict):
        raise ConfigLoadError(
            f"Top-level config structure must be a dictionary/object, got {type(data).__name__}."
        )

    return data


def save_config(config: Dict[str, Any], output_path: str | Path) -> Path:
    """Save a config dictionary as YAML or JSON.

    Parameters
    ----------
    config:
        Configuration dictionary to save.
    output_path:
        Destination path ending in .yaml/.yml or .json.
    """
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ConfigLoadError(
            f"Unsupported output format: {path.suffix}. "
            f"Expected one of: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            if yaml is None:
                raise ConfigLoadError(
                    "PyYAML is required to write YAML files. Install it with `pip install pyyaml`."
                )
            with path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, sort_keys=False)
        else:
            with path.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
    except Exception as exc:
        raise ConfigLoadError(f"Failed to write config file {path}: {exc}") from exc

    return path
