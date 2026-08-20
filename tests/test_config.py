import json

from app.config import load_config


def test_missing_config_is_recreated(tmp_path):
    path = tmp_path / "config.json"
    config = load_config(path)
    assert config["backend"] == "simulator"
    assert json.loads(path.read_text())["measurement_duration_s"] == 30


def test_partial_config_is_merged(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"sound": {"enabled": true}}')
    config = load_config(path)
    assert config["sound"]["enabled"] is True
    assert "volume" in config["sound"]
