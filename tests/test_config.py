"""Config-driven installs: file/env/relative-path resolution + threshold wiring."""
import os
import pytest
import yaml

from indexer.config import IndexerConfig, load_config, coerce_config, CONFIG_ENV_VAR
from indexer.rules.engine import RuleEngine
from indexer.workqueue import WorkQueueManager, WorkQueueItem


def _write_config(dirpath, data):
    path = os.path.join(dirpath, "tessera_indexer.yaml")
    with open(path, "w") as f:
        yaml.safe_dump(data, f)
    return path


def test_defaults_resolve_package_taxonomy():
    cfg = IndexerConfig.load()
    assert os.path.exists(cfg.taxonomy_path), cfg.taxonomy_path
    assert os.path.isdir(cfg.schema_dir), cfg.schema_dir
    assert cfg.hitl_threshold == 0.85
    assert cfg._source is None
    # Defaults must actually load the 6 schemas
    engine = RuleEngine()
    assert len(engine.schemas) == 6


def test_yaml_overrides_with_relative_resolution(tmp_path):
    cfg_file = _write_config(tmp_path, {
        "queue_dir": "queues",
        "review_dir": "review",
        "hitl_threshold": 0.9,
    })
    cfg = load_config(cfg_file)
    assert cfg.queue_dir == str(tmp_path / "queues")
    assert cfg.review_dir == str(tmp_path / "review")
    assert cfg.hitl_threshold == 0.9
    assert cfg._source == cfg_file
    # Unset keys keep built-in defaults
    assert cfg.taxonomy_path == IndexerConfig.defaults().taxonomy_path


def test_env_var_config(tmp_path, monkeypatch):
    cfg_file = _write_config(tmp_path, {"queue_dir": "env_queues"})
    monkeypatch.setenv(CONFIG_ENV_VAR, cfg_file)
    cfg = load_config()
    assert cfg.queue_dir == str(tmp_path / "env_queues")


def test_cwd_config_file(tmp_path, monkeypatch):
    _write_config(tmp_path, {"hitl_threshold": 0.75})
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(CONFIG_ENV_VAR, raising=False)
    cfg = load_config()
    assert cfg.hitl_threshold == 0.75


def test_unknown_key_rejected(tmp_path):
    cfg_file = _write_config(tmp_path, {"nonsense_key": 1})
    with pytest.raises(ValueError, match="Unknown config keys"):
        load_config(cfg_file)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "nope.yaml"))


def test_coerce_accepts_none_path_and_object(tmp_path):
    assert coerce_config(None) is None
    cfg_file = _write_config(tmp_path, {"queue_dir": "q"})
    loaded = coerce_config(cfg_file)
    assert isinstance(loaded, IndexerConfig)
    assert coerce_config(loaded) is loaded
    with pytest.raises(TypeError):
        coerce_config(123)


def test_workqueue_threshold_from_config(tmp_path):
    cfg_file = _write_config(tmp_path, {"queue_dir": "queues", "hitl_threshold": 0.9})
    wq = WorkQueueManager(config=cfg_file)
    assert wq.queue_dir == str(tmp_path / "queues")
    assert wq.hitl_threshold == 0.9

    item = WorkQueueItem(
        email_id="e1", task_id="t1", policy_number="POL-12345678",
        client_name="Jane", main_type="x", sub_type="repurchase",
        pages="1", confidence=0.88,
    )
    queue = wq.route(item)
    assert queue == "policy_admin"
    assert item.status == "review"  # 0.88 < 0.9 threshold

    # Default threshold (0.85) would have auto-routed the same item
    item2 = WorkQueueItem(
        email_id="e2", task_id="t2", policy_number="POL-12345678",
        client_name="Jane", main_type="x", sub_type="repurchase",
        pages="1", confidence=0.88,
    )
    default_wq = WorkQueueManager(queue_dir=str(tmp_path / "dq"))
    default_wq.route(item2)
    assert item2.status == "pending"  # 0.88 >= 0.85


def test_rule_engine_accepts_config_path(tmp_path):
    cfg_file = _write_config(tmp_path, {"hitl_threshold": 0.9})
    engine = RuleEngine(config=cfg_file)  # path string, not an object
    assert engine.config.hitl_threshold == 0.9
    assert len(engine.schemas) == 6


def test_explicit_args_override_config(tmp_path):
    cfg_file = _write_config(tmp_path, {"queue_dir": "from_config"})
    engine = RuleEngine(config=cfg_file)
    assert engine.config.queue_dir == str(tmp_path / "from_config")
    # Explicit constructor args still win for taxonomy/schema resolution
    defaults = IndexerConfig.defaults()
    engine2 = RuleEngine(config=cfg_file, taxonomy_path=defaults.taxonomy_path,
                         schema_dir=defaults.schema_dir)
    assert str(engine2.taxonomy_path) == defaults.taxonomy_path
