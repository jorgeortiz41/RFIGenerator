from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import pandas as pd


def save_file(input_file, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_file, output_path)
    return output_path


def save_data(data, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if isinstance(data, str):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(data)
    elif hasattr(data, 'to_csv'):
        data.to_csv(output_path, index=False)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(_json_safe(data), f, indent=2)
    
    return output_path


def save_pipeline_outputs(
    clean_data: pd.DataFrame | list[pd.DataFrame],
    contaminated_data: pd.DataFrame | list[pd.DataFrame],
    rfi_infos: list[list[dict[str, Any]]],
    sources: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Save the datasets and metadata produced by the CLI pipeline.

    The CLI produces clean radiometry datasets first, then mixes generated RFI
    sources into copies of those datasets. This exporter keeps those outputs
    separate so downstream analysis can compare clean and contaminated data.
    """
    export_cfg = config.get("export", {})
    output_dir = Path(export_cfg.get("directory", "outputs/"))
    output_dir.mkdir(parents=True, exist_ok=True)

    formats = export_cfg.get("formats", {})
    save_csv = formats.get("csv", True)
    save_xlsx = formats.get("xlsx", False)
    filenames = export_cfg.get("filenames", {})

    saved: dict[str, Any] = {
        "clean": [],
        "contaminated": [],
        "metadata": None,
    }

    clean_frames = _dataframes_as_list(clean_data)
    contaminated_frames = _dataframes_as_list(contaminated_data)

    if len(clean_frames) != len(contaminated_frames):
        raise ValueError(
            "Clean and contaminated dataset counts differ: "
            f"{len(clean_frames)} != {len(contaminated_frames)}"
        )

    if export_cfg.get("save_clean", True):
        saved["clean"] = _save_dataframe_collection(
            clean_frames,
            output_dir,
            filenames.get("clean", "clean"),
            save_csv=save_csv,
            save_xlsx=save_xlsx,
        )

    if export_cfg.get("save_contaminated", True):
        saved["contaminated"] = _save_dataframe_collection(
            contaminated_frames,
            output_dir,
            filenames.get("contaminated", "contaminated"),
            save_csv=save_csv,
            save_xlsx=save_xlsx,
        )

    if export_cfg.get("save_metadata", True):
        metadata_path = output_dir / f"{filenames.get('metadata', 'metadata')}.json"
        metadata = {
            "project": config.get("project", {}),
            "run": config.get("run", {}),
            "radiometry": config.get("radiometry", {}),
            "composition": config.get("composition", {}),
            "export": export_cfg,
            "dataset_count": len(clean_frames),
            "rfi_source_count": len(sources),
            "rfi_sources": sources,
            "rfi_infos": rfi_infos,
            "saved_files": saved,
        }
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(_json_safe(metadata), f, indent=2)
        saved["metadata"] = str(metadata_path)

    return saved


def _dataframes_as_list(data: pd.DataFrame | list[pd.DataFrame]) -> list[pd.DataFrame]:
    if isinstance(data, pd.DataFrame):
        return [data]
    if isinstance(data, list) and all(isinstance(item, pd.DataFrame) for item in data):
        return data
    raise TypeError("Expected a pandas DataFrame or list of pandas DataFrames.")


def _save_dataframe_collection(
    dataframes: list[pd.DataFrame],
    output_dir: Path,
    filename_prefix: str,
    *,
    save_csv: bool,
    save_xlsx: bool,
) -> list[dict[str, str]]:
    saved_files = []
    multiple = len(dataframes) > 1

    for index, dataframe in enumerate(dataframes):
        suffix = f"_{index:03d}" if multiple else ""
        dataset_files = {}

        if save_csv:
            csv_path = output_dir / f"{filename_prefix}{suffix}.csv"
            dataframe.to_csv(csv_path, index=False)
            dataset_files["csv"] = str(csv_path)

        if save_xlsx:
            xlsx_path = output_dir / f"{filename_prefix}{suffix}.xlsx"
            dataframe.to_excel(xlsx_path, index=False)
            dataset_files["xlsx"] = str(xlsx_path)

        saved_files.append(dataset_files)

    return saved_files


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value
