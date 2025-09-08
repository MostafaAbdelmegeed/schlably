# src/scripts/make_all_ORs_eligible.py
from __future__ import annotations

import argparse
from pathlib import Path

from src.utils.file_handler.config_handler import ConfigHandler
from src.utils.file_handler.data_handler import DataHandler


def _resolve_config_path(user_path: str) -> str:
    """
    Accept absolute/relative paths. If the given path doesn't exist,
    also try prefixing 'config/' (since many Schlably calls assume that root).
    """
    p = Path('config') / user_path
    if p.exists():
        return Path(user_path)
    raise FileNotFoundError(
        f"Config file not found at:\n  {p.resolve()}\n"
        "Pass a valid path to the data-generation YAML with -fp/--config."
    )


def main():
    ap = argparse.ArgumentParser(
        description="Force every task to be eligible on all machines for a given dataset."
    )
    ap.add_argument(
        "-fp", "--config",
        required=True,
        help="Path to the data-generation YAML (absolute or relative; "
             "both 'config/...yaml' and '...yaml' are accepted)."
    )
    ap.add_argument(
        "-o", "--out",
        default=None,
        help=("Optional output path (relative to data/instances/). "
              "May include subdirs like 'fjssp/foo_allORs.pkl'. "
              "Default: original instances_file with '_allORs' suffix.")
    )
    args = ap.parse_args()

    cfg_path = _resolve_config_path(args.config)
    cfg = ConfigHandler.get_config(cfg_path)

    # Load the dataset referenced by the YAML's `instances_file`
    try:
        instances = DataHandler.load_instances_data_file(cfg)
    except AssertionError as e:
        # Most common cause: dataset hasn't been generated yet.
        hint = (
            "Dataset not found. Generate it first with:\n"
            f"  python -m src.data_generator.instance_factory -fp {cfg_path}"
        )
        raise FileNotFoundError(hint) from e

    # Make every task eligible on all machines
    M = int(cfg["num_machines"])
    all_machines = list(range(M))
    for inst in instances:
        for task in inst:
            task.machines = all_machines

    # Decide output filename
    if args.out:
        out_rel = args.out  # user provided (can include subfolders)
    else:
        inst_file = Path(cfg["instances_file"])
        out_rel = str(inst_file.with_name(inst_file.stem + "_allORs.pkl"))

    # Save under data/instances/<out_rel>
    cfg_out = dict(cfg)
    cfg_out["instances_file"] = out_rel
    DataHandler.save_instances_data_file(cfg_out, instances)

    print(f"✅ Wrote: data/instances/{out_rel}")


if __name__ == "__main__":
    main()
