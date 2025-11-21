import pytest

from scripts.macos_share_action import build_command_from_inputs


def test_build_command_with_files():
    command = build_command_from_inputs(
        files=["/tmp/article.pdf", "/tmp/screenshot.png"],
        url=None,
        text=None,
        title="Research Notes",
        database="research",
        tags="ai,notion",
        python_cmd="python",
    )

    assert command == [
        "python",
        "-m",
        "src.main",
        "add-note",
        "--database",
        "research",
        "--title",
        "Research Notes",
        "--tags",
        "ai,notion",
        "--file",
        "/tmp/article.pdf",
        "--file",
        "/tmp/screenshot.png",
    ]


def test_build_command_with_url():
    command = build_command_from_inputs(
        files=[],
        url="https://example.com/notes",
        text=None,
        title=None,
        database=None,
        tags=None,
        python_cmd="python3",
    )

    assert command == [
        "python3",
        "-m",
        "src.main",
        "add-note",
        "--url",
        "https://example.com/notes",
    ]


def test_build_command_with_text():
    text_snippet = "Notes captured via share sheet"
    command = build_command_from_inputs(
        files=[],
        url=None,
        text=text_snippet,
        title="Quick Note",
        database=None,
        tags=None,
        python_cmd="python3",
    )

    assert command == [
        "python3",
        "-m",
        "src.main",
        "add-note",
        "--title",
        "Quick Note",
        "--text",
        text_snippet,
    ]


def test_build_command_requires_single_input():
    with pytest.raises(ValueError):
        build_command_from_inputs(
            files=["/tmp/one.md"],
            url="https://example.com",
            text=None,
            title=None,
            database=None,
            tags=None,
            python_cmd="python3",
        )


def test_build_command_requires_at_least_one_input():
    with pytest.raises(ValueError):
        build_command_from_inputs(
            files=[],
            url=None,
            text=None,
            title=None,
            database=None,
            tags=None,
            python_cmd="python3",
        )

