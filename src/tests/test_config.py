import json

import pytest

from src.config.config_loader import ConfigLoadError, load_config, save_config
from src.config.config_parser import ConfigValidationError, parse_and_validate_config


def test_parse_and_validate_config_applies_defaults():
    config = parse_and_validate_config({})

    assert config["project"]["name"] == "RFIGen"
    assert config["run"]["seed"] == 12345
    assert config["composition"]["inject_rfi"] is True
    assert config["rfi_sources"] == []


def test_parse_and_validate_config_accepts_valid_rfi_source():
    raw_config = {
        "rfi_sources": [
            {
                "id": "rfi_nb_001",
                "type": "narrowband",
                "enabled": True,
                "center_offset_mhz": 12.0,
                "bandwidth_mhz": 2.0,
                "power_dbm": -72.0,
                "persistence": 1.0,
                "modulation": "none",
            }
        ]
    }

    config = parse_and_validate_config(raw_config)

    assert config["rfi_sources"][0]["id"] == "rfi_nb_001"


@pytest.mark.parametrize(
    "raw_config",
    [
        {"run": {"seed": "123"}},
        {"run": {"n_datasets": 0}},
        {"radiometry": {"noise_std_k": -1.0}},
        {"composition": {"inject_rfi": "yes"}},
        {"export": {"directory": ""}},
        {"rfi_sources": "not-a-list"},
    ],
)
def test_parse_and_validate_config_rejects_invalid_values(raw_config):
    with pytest.raises(ConfigValidationError):
        parse_and_validate_config(raw_config)


def test_load_config_reads_json_file(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"run": {"seed": 7}}), encoding="utf-8")

    assert load_config(config_path) == {"run": {"seed": 7}}


def test_load_config_rejects_missing_file(tmp_path):
    with pytest.raises(ConfigLoadError):
        load_config(tmp_path / "missing.json")


def test_save_config_writes_json_file(tmp_path):
    output_path = tmp_path / "saved.json"

    saved_path = save_config({"project": {"name": "demo"}}, output_path)

    assert saved_path == output_path.resolve()
    assert json.loads(output_path.read_text(encoding="utf-8")) == {
        "project": {"name": "demo"}
    }
