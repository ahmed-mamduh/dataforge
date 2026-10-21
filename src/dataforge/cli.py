"""CLI entry point for DataForge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dataforge.config import MappingConfigError, PipelineConfig, load_mapping_config
from dataforge.engine import run_pipeline


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="dataforge",
        description="DataForge — CSV & Excel data cleaning engine",
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        type=Path,
        help="Input CSV or Excel files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--mapping-config",
        type=Path,
        default=None,
        help="Optional JSON file with custom column mappings",
    )

    args = parser.parse_args(argv)

    kwargs: dict = {
        "input_files": args.input,
        "output_dir": args.output,
    }

    if args.mapping_config:
        try:
            kwargs["column_mappings"] = load_mapping_config(args.mapping_config)
        except MappingConfigError as e:
            print(f"Error loading mapping config: {e}", file=sys.stderr)
            sys.exit(1)

    config = PipelineConfig(**kwargs)

    print(f"DataForge — processing {len(config.input_files)} file(s)")
    for f in config.input_files:
        print(f"  {f}")

    result = run_pipeline(config)

    print(f"\nResults:")
    print(f"  Input rows:  {result.stats['input_rows']}")
    print(f"  Accepted:    {result.stats['accepted']}")
    print(f"  Rejected:    {result.stats['rejected']}")
    print(f"  Duplicates:  {result.stats['duplicates']}")

    print(f"\nOutputs written to: {config.output_dir}")
    for name, path in result.output_paths.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
