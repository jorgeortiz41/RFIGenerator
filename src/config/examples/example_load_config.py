from pathlib import Path

from config.config_loader import load_config
from config.config_parser import ConfigValidationError, parse_and_validate_config


def main() -> None:
    config_path = Path("config/examples/base_config.yaml").resolve()
    raw_config = load_config(config_path)

    try:
        config = parse_and_validate_config(raw_config)
    except ConfigValidationError as exc:
        print(f"Config validation failed: {exc}")
        raise SystemExit(1) from exc

    print("Config loaded successfully.")
    print(f"Project: {config['project']['name']} ({config['project']['profile']})")
    print(f"Center frequency: {config['frequency']['center_ghz']} GHz")
    print(f"Configured RFI sources: {len(config['rfi_sources'])}")
    print("Full config:")
    print(config)


if __name__ == "__main__":
    main()
