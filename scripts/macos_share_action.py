"""Helper entry point that bridges macOS share workflows to the Notion CLI."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bridge macOS Share/Quick Action inputs into notion-note-creator."
    )
    parser.add_argument(
        "--files",
        nargs="*",
        type=Path,
        default=[],
        help="Files dropped into the Quick Action or share sheet.",
    )
    parser.add_argument("--url", type=str, help="URL shared into the workflow.")
    parser.add_argument(
        "--text",
        type=str,
        help="Explicit text argument (shortcuts may pass longer text this way).",
    )
    parser.add_argument(
        "--title",
        type=str,
        help="Override the AI-generated title for the resulting Notion page.",
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Target database name (as defined in config/config.yaml).",
    )
    parser.add_argument(
        "--tags",
        type=str,
        help="Comma-separated tags (forwarded to the CLI for future use).",
    )
    return parser.parse_args()


def read_stdin_text() -> Optional[str]:
    if sys.stdin.isatty():
        return None
    data = sys.stdin.read()
    text = data.strip()
    return text if text else None


def build_command_from_inputs(
    *,
    files: Iterable[str],
    url: Optional[str],
    text: Optional[str],
    title: Optional[str],
    database: Optional[str],
    tags: Optional[str],
    python_cmd: Optional[str] = None,
) -> List[str]:
    file_list = list(files)
    inputs = sum(map(bool, [file_list, url, text]))

    if inputs == 0:
        raise ValueError("Provide at least one of files, url, or text to import.")
    if inputs > 1:
        raise ValueError("Share helper accepts only one input type per invocation.")

    command = [
        python_cmd or sys.executable,
        "-m",
        "src.main",
        "add-note",
    ]

    if database:
        command.extend(["--database", database])
    if title:
        command.extend(["--title", title])
    if tags:
        command.extend(["--tags", tags])

    if file_list:
        for file_path in file_list:
            command.extend(["--file", str(Path(file_path))])
    elif url:
        command.extend(["--url", url])
    elif text:
        command.extend(["--text", text])

    return command


def run_command(command: List[str]) -> None:
    logger.info("Running: %s", " ".join(command))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        logger.error("Notion CLI failed: %s", exc)
        sys.exit(exc.returncode)


def main() -> None:
    args = parse_arguments()
    stdin_text = read_stdin_text()
    provided_text = args.text or stdin_text

    command = build_command_from_inputs(
        files=[str(path) for path in args.files],
        url=args.url,
        text=provided_text,
        title=args.title,
        database=args.database,
        tags=args.tags,
    )
    run_command(command)


if __name__ == "__main__":
    main()

