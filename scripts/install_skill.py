#!/usr/bin/env python3
"""Offline, non-overwriting installation of the bundled Agent Skill."""

import argparse
from pathlib import Path
import shutil

NAME = "zotero-10"
ROOT = Path(__file__).resolve().parents[1]


def install(destination, source=None):
    source = Path(source) if source else ROOT / "plugins" / NAME / "skills" / NAME
    if not (source / "SKILL.md").is_file():
        raise ValueError("Source does not contain SKILL.md")
    if source.is_symlink() or any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("Refusing a source containing symbolic links")
    target = Path(destination).expanduser() / NAME
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"Already exists; nothing overwritten: {target}")
    if target.resolve() == source.resolve() or source.resolve() in target.resolve().parents:
        raise ValueError("Destination must be outside the source Skill")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=Path.home() / ".agents" / "skills",
                        help="Parent skills directory (default: ~/.agents/skills)")
    args = parser.parse_args()
    try:
        target = install(args.dest)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Installation stopped: {error}\n")
    print(f"Installed: {target}\nStart a new chat; restart the host if not discovered.")


if __name__ == "__main__":
    main()
