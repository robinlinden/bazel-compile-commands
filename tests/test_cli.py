import pytest

from bazel_compile_commands.cli import _action_to_compile_command, _parse_args


# Parametrized test for action to compile command for both Linux and MSVC:
@pytest.mark.parametrize(
    "action, expected",
    [
        # Linux/gcc
        (
            {
                "arguments": [
                    "gcc",
                    "-iquote",
                    "external/foo",
                    "-isystem",
                    "external/bar",
                    "-c",
                    "src/foo.cc",
                ]
            },
            {
                "directory": "/good/project",
                "arguments": [
                    "gcc",
                    "-iquote",
                    "bazel-project/external/foo",
                    "-isystem",
                    "bazel-project/external/bar",
                    "-c",
                    "src/foo.cc",
                ],
                "file": "src/foo.cc",
            },
        ),
        (
            # -c src.cc before arguments that should be patched.
            {
                "arguments": [
                    "clang++",
                    "-c",
                    "external/foo/src.cc",
                    "-isystem",
                    "external/bar",
                ]
            },
            {
                "directory": "/good/project",
                "arguments": [
                    "clang++",
                    "-c",
                    "bazel-project/external/foo/src.cc",
                    "-isystem",
                    "bazel-project/external/bar",
                ],
                "file": "bazel-project/external/foo/src.cc",
            },
        ),
        (
            # compiler in external/, --sysroot, and -B.
            {
                "arguments": [
                    "external/some/compiler",
                    "--sysroot=external/sysroot",
                    "-Bexternal/toolchain",
                    "--sysroot",
                    "external/split-sysroot",
                    "-B",
                    "external/split-toolchain",
                    "-c",
                    "src/foo.cc",
                ]
            },
            {
                "directory": "/good/project",
                "arguments": [
                    "bazel-project/external/some/compiler",
                    "--sysroot=bazel-project/external/sysroot",
                    "-Bbazel-project/external/toolchain",
                    "--sysroot",
                    "bazel-project/external/split-sysroot",
                    "-B",
                    "bazel-project/external/split-toolchain",
                    "-c",
                    "src/foo.cc",
                ],
                "file": "src/foo.cc",
            },
        ),
        # Windows/MSVC
        (
            {
                "arguments": [
                    "cl.exe",
                    "/Iexternal/foo",
                    "/external:Iexternal/bar",
                    "/c",
                    "src/foo.cc",
                ]
            },
            {
                "directory": "/good/project",
                "arguments": [
                    "cl.exe",
                    "/Ibazel-project/external/foo",
                    "/external:Ibazel-project/external/bar",
                    "/c",
                    "src/foo.cc",
                ],
                "file": "src/foo.cc",
            },
        ),
    ],
)
def test_action_to_compile_command(action, expected):
    result = _action_to_compile_command(
        "/good/project",
        "project",
        action,
    )
    assert result == expected


def test_action_to_compile_command_excludes_matching_argument():
    action = {
        "arguments": [
            "clang++",
            "-fsyntax-only",
            "-c",
            "src/foo.cc",
        ]
    }

    result = _action_to_compile_command(
        "/good/project",
        "project",
        action,
        ["-fsyntax-only"],
    )

    assert result is None


def test_action_to_compile_command_keeps_nonmatching_argument():
    action = {
        "arguments": [
            "clang++",
            "-Wall",
            "-c",
            "src/foo.cc",
        ]
    }

    result = _action_to_compile_command(
        "/good/project",
        "project",
        action,
        ["-fsyntax-only"],
    )

    assert result == {
        "directory": "/good/project",
        "arguments": ["clang++", "-Wall", "-c", "src/foo.cc"],
        "file": "src/foo.cc",
    }


def test_parse_args_accepts_repeated_exclude_arguments():
    args = _parse_args(
        [
            "--exclude-if-has-argument=-fsyntax-only",
            "--exclude-if-has-argument=-Werror",
            "--",
            "--config=myconfig",
        ]
    )
    assert args.exclude_if_has_argument == ["-fsyntax-only", "-Werror"]
    assert args.aquery_args == ["--config=myconfig"]


def test_parse_args_accepts_aquery_args_after_separator():
    args = _parse_args(["--", "--config=myconfig", "//foo"])
    assert args.aquery_args == ["--config=myconfig", "//foo"]


def test_parse_args_allows_no_aquery_args():
    args = _parse_args([])
    assert args.aquery_args == []


def test_parse_args_requires_separator_for_aquery_args():
    with pytest.raises(SystemExit) as exc_info:
        _parse_args(["//foo"])

    assert exc_info.value.code == 2


def test_parse_args_rejects_separator_after_aquery_args():
    with pytest.raises(SystemExit) as exc_info:
        _parse_args(["asdf", "--"])

    assert exc_info.value.code == 2
