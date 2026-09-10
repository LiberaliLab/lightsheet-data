from __future__ import annotations

import argparse

from . import clear_cache, download, info


def main() -> None:
    parser = argparse.ArgumentParser(prog="lsdata")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("info", help="List available datasets")

    download_parser = subparsers.add_parser("download", help="Download a dataset")
    download_parser.add_argument("name", help="Dataset name, e.g. 001-mini")
    download_parser.add_argument("--version", default=None, help="Dataset version (default: latest)")

    clear_parser = subparsers.add_parser("clear-cache", help="Delete cached dataset(s)")
    clear_parser.add_argument("--name", default=None, help="Only clear this dataset (default: all)")
    clear_parser.add_argument("--version", default=None, help="Only clear this version (default: all)")

    args = parser.parse_args()

    if args.command == "info":
        info()
    elif args.command == "download":
        path = download(args.name, args.version)
        print(path)
    elif args.command == "clear-cache":
        for path in clear_cache(args.name, args.version):
            print(f"Removed {path}")
