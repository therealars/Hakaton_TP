from __future__ import annotations

import argparse
from pathlib import Path

from .processor import MailProcessor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sort corporate inbox files by meaning.")
    parser.add_argument("--input", required=True, type=Path, help="Directory with incoming files")
    parser.add_argument("--output", required=True, type=Path, help="Directory for sorted files")
    parser.add_argument("--log-dir", required=True, type=Path, help="Directory for processing logs")
    parser.add_argument(
        "--mode",
        choices=("copy", "move"),
        default="copy",
        help="copy keeps source files intact; move relocates them",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    processor = MailProcessor()
    summary = processor.process(
        input_dir=args.input,
        output_dir=args.output,
        log_dir=args.log_dir,
        mode=args.mode,
    )

    print("Mail processing finished")
    print(f"Total files: {summary.total_files}")
    print(f"Output directory: {summary.output_dir}")
    print(f"Processing log: {summary.log_file}")
    print(f"Statistics: {summary.stats_file}")
    print("Categories:")
    for category, count in summary.categories.items():
        print(f"  {category}: {count}")
    print("Read statuses:")
    for status, count in summary.statuses.items():
        print(f"  {status}: {count}")
    return 0