"""Config-driven installs for Tessera AI Indexer.

All install-specific paths and thresholds live in one place:

- taxonomy path & schema dir   (schemas bundled with the wheel by default)
- Tier-4 model paths           (ONNX dir + TF-IDF joblib)
- runtime data dirs            (work queues, human review, inbox)
- HITL confidence threshold    (below it -> routed to human review)

Config file resolution (first match wins):
  1. explicit ``path`` argument (e.g. CLI ``--config``)
  2. ``$TESSERA_INDEXER_CONFIG`` environment variable
  3. ``./tessera_indexer.yaml`` in the working directory
  4. built-in defaults only (package-relative taxonomy, cwd-relative data)

Relative paths in a user config file resolve against the config file's own
directory, so an on-prem deploy dir (config.yaml + models/ + data/) works
from any working directory.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, fields, asdict
from pathlib import Path
from typing import Optional

import yaml

CONFIG_ENV_VAR = "TESSERA_INDEXER_CONFIG"
DEFAULT_CONFIG_FILENAME = "tessera_indexer.yaml"


def _package_dir() -> Path:
    return Path(__file__).resolve().parent


@dataclass
class IndexerConfig:
    taxonomy_path: str = ""
    schema_dir: str = ""
    onnx_model_dir: str = "models/tessera-encoder-v1"
    tfidf_model_path: str = "models/tier4_model.joblib"
    queue_dir: str = "data/workqueues"
    review_dir: str = "data/human_review"
    inbox_dir: str = "data/inbox"
    hitl_threshold: float = 0.85
    # Where this config was loaded from (path or None for built-in defaults).
    # Not user-settable; informational only.
    _source: Optional[str] = None

    @classmethod
    def defaults(cls) -> "IndexerConfig":
        """Built-in defaults: taxonomy bundled with the package, runtime data
        relative to the working directory."""
        pkg = _package_dir()
        return cls(
            taxonomy_path=str(pkg / "taxonomy" / "taxonomy.yaml"),
            schema_dir=str(pkg / "taxonomy" / "schemas"),
        )

    @classmethod
    def load(cls, path: Optional[str] = None) -> "IndexerConfig":
        """Load effective config: user file (arg > env > cwd) merged over defaults.

        Returns defaults-only when no config file exists anywhere.
        """
        cfg = cls.defaults()

        if path is None:
            path = os.environ.get(CONFIG_ENV_VAR)
        if path is None:
            cwd_candidate = Path.cwd() / DEFAULT_CONFIG_FILENAME
            if cwd_candidate.exists():
                path = str(cwd_candidate)

        if not path:
            return cfg

        config_file = Path(path).expanduser()
        if not config_file.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_file} (set {CONFIG_ENV_VAR} or pass --config)"
            )

        with open(config_file, "r") as f:
            raw = yaml.safe_load(f) or {}

        unknown = set(raw) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown config keys: {sorted(unknown)} (valid: {', '.join(f.name for f in fields(cls))})")

        base_dir = config_file.parent
        for key, value in raw.items():
            current = getattr(cfg, key)
            if isinstance(current, str) and isinstance(value, str) and value:
                p = Path(value).expanduser()
                if not p.is_absolute():
                    p = base_dir / p
                setattr(cfg, key, str(p))
            elif isinstance(current, float) and isinstance(value, (int, float)):
                setattr(cfg, key, float(value))
            else:
                setattr(cfg, key, value)

        cfg._source = str(config_file)
        return cfg

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if not k.startswith("_")}


def coerce_config(config) -> Optional["IndexerConfig"]:
    """Accept None, a config file path, or an IndexerConfig — return an
    IndexerConfig (or None for None, meaning 'use built-in defaults')."""
    if config is None or isinstance(config, IndexerConfig):
        return config
    if isinstance(config, (str, os.PathLike)):
        return IndexerConfig.load(str(config))
    raise TypeError(f"config must be a path or IndexerConfig, got {type(config).__name__}")


def load_config(path: Optional[str] = None) -> IndexerConfig:
    """Convenience wrapper (module-level) around ``IndexerConfig.load``."""
    return IndexerConfig.load(path)
